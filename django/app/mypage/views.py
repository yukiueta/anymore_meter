import jwt
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncHour

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from app.meters.models import Meter, MeterAssignment
from app.readings.models import MeterReading, DailySummary, MonthlySummary


class CustomerAuthMixin:
    """マイページ用JWT認証ミックスイン"""
    
    def get_customer_id(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('JWT '):
            return None
        
        token = auth_header[4:]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            if payload.get('type') != 'customer':
                return None
            return payload.get('customer_id')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None


class MypageReadingsView(CustomerAuthMixin, APIView):
    """マイページ用発電データ取得API"""
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        customer_id = self.get_customer_id(request)
        if not customer_id:
            return Response(
                {'message': '認証が必要です'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        period = request.query_params.get('period', 'month')
        date_str = request.query_params.get('date')
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        except ValueError:
            target_date = datetime.now().date()

        # メーター取得
        assignment = MeterAssignment.objects.filter(
            project_id=customer_id,
            end_date__isnull=True
        ).select_related('meter').first()

        if not assignment:
            return Response({
                'chart': [],
                'total_generation': 0,
                'total_sold': 0,
                'total_self': 0,
                'meter_id': ''
            })

        meter = assignment.meter

        if period == 'day':
            data = self._get_daily_data(meter, target_date)
        elif period == 'week':
            data = self._get_weekly_data(meter, target_date)
        elif period == 'year':
            data = self._get_yearly_data(meter, target_date)
        else:  # month
            data = self._get_monthly_data(meter, target_date)

        data['meter_id'] = meter.meter_id
        return Response(data)

    def _get_daily_data(self, meter, target_date):
        """日次: 時間ごとのデータ（24時間）"""
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        readings = MeterReading.objects.filter(
            meter=meter,
            recorded_at__gte=start,
            recorded_at__lt=end
        ).annotate(
            hour=TruncHour('recorded_at')
        ).values('hour').annotate(
            sold=Sum('export_kwh'),
            pv=Sum('pv_energy_kwh')
        ).order_by('hour')

        chart = []
        for i in range(24):
            hour_data = next((r for r in readings if r['hour'].hour == i), None)
            sold = float(hour_data['sold'] or 0) if hour_data else 0
            pv = float(hour_data['pv'] or 0) if hour_data else 0
            self_consumption = max(0, pv - sold)
            chart.append({
                'label': str(i),
                'sold': round(sold, 2),
                'self': round(self_consumption, 2)
            })

        total_sold = sum(c['sold'] for c in chart)
        total_self = sum(c['self'] for c in chart)

        return {
            'chart': chart,
            'total_generation': round(total_sold + total_self, 2),
            'total_sold': round(total_sold, 2),
            'total_self': round(total_self, 2)
        }

    def _get_weekly_data(self, meter, target_date):
        """週次: 日ごとのデータ（7日間）"""
        # 週の開始日（月曜日）
        start = target_date - timedelta(days=target_date.weekday())
        end = start + timedelta(days=7)

        summaries = DailySummary.objects.filter(
            meter=meter,
            date__gte=start,
            date__lt=end
        ).order_by('date')

        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        chart = []
        
        for i in range(7):
            day = start + timedelta(days=i)
            summary = next((s for s in summaries if s.date == day), None)
            sold = float(summary.total_export_kwh or 0) if summary else 0
            pv = float(summary.total_pv_kwh or 0) if summary else 0
            self_consumption = max(0, pv - sold)
            chart.append({
                'label': weekdays[i],
                'sold': round(sold, 2),
                'self': round(self_consumption, 2)
            })

        total_sold = sum(c['sold'] for c in chart)
        total_self = sum(c['self'] for c in chart)

        return {
            'chart': chart,
            'total_generation': round(total_sold + total_self, 2),
            'total_sold': round(total_sold, 2),
            'total_self': round(total_self, 2)
        }

    def _get_monthly_data(self, meter, target_date):
        """月次: 日ごとのデータ（1ヶ月）"""
        import calendar
        
        year = target_date.year
        month = target_date.month
        _, days_in_month = calendar.monthrange(year, month)
        
        start = target_date.replace(day=1)
        end = start + timedelta(days=days_in_month)

        summaries = DailySummary.objects.filter(
            meter=meter,
            date__gte=start,
            date__lt=end
        ).order_by('date')

        chart = []
        for i in range(1, days_in_month + 1):
            day = start.replace(day=i)
            summary = next((s for s in summaries if s.date == day), None)
            sold = float(summary.total_export_kwh or 0) if summary else 0
            pv = float(summary.total_pv_kwh or 0) if summary else 0
            self_consumption = max(0, pv - sold)
            chart.append({
                'label': str(i),
                'sold': round(sold, 2),
                'self': round(self_consumption, 2)
            })

        total_sold = sum(c['sold'] for c in chart)
        total_self = sum(c['self'] for c in chart)

        return {
            'chart': chart,
            'total_generation': round(total_sold + total_self, 2),
            'total_sold': round(total_sold, 2),
            'total_self': round(total_self, 2)
        }

    def _get_yearly_data(self, meter, target_date):
        """年次: 月ごとのデータ（12ヶ月）"""
        year = target_date.year

        summaries = MonthlySummary.objects.filter(
            meter=meter,
            year_month__startswith=str(year)
        ).order_by('year_month')

        chart = []
        for i in range(1, 13):
            year_month = f"{year}-{str(i).zfill(2)}"
            summary = next((s for s in summaries if s.year_month == year_month), None)
            sold = float(summary.total_export_kwh or 0) if summary else 0
            pv = float(summary.total_pv_kwh or 0) if summary else 0
            self_consumption = max(0, pv - sold)
            chart.append({
                'label': f'{i}月',
                'sold': round(sold, 2),
                'self': round(self_consumption, 2)
            })

        total_sold = sum(c['sold'] for c in chart)
        total_self = sum(c['self'] for c in chart)

        return {
            'chart': chart,
            'total_generation': round(total_sold + total_self, 2),
            'total_sold': round(total_sold, 2),
            'total_self': round(total_self, 2)
        }