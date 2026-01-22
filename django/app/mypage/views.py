import jwt
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from app.meters.models import MeterAssignment
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
            return Response({'message': '認証が必要です'}, status=status.HTTP_401_UNAUTHORIZED)

        period = request.query_params.get('period', 'month')
        date_str = request.query_params.get('date')
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else datetime.now().date()
        except ValueError:
            target_date = datetime.now().date()

        assignment = MeterAssignment.objects.filter(
            project_id=customer_id,
            end_date__isnull=True
        ).select_related('meter').first()

        if not assignment:
            return Response({
                'chart': [],
                'total_generation': 0,
                'total_export': 0,
                'total_self_consumption': 0,
                'meter_id': ''
            })

        meter = assignment.meter

        if period == 'day':
            data = self._get_daily_data(meter, target_date)
        elif period == 'week':
            data = self._get_weekly_data(meter, target_date)
        elif period == 'year':
            data = self._get_yearly_data(meter, target_date)
        else:
            data = self._get_monthly_data(meter, target_date)

        data['meter_id'] = meter.meter_id
        return Response(data)

    def _get_daily_data(self, meter, target_date):
        """日次: 時間ごとのデータ（24時間）"""
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        readings = list(MeterReading.objects.filter(
            meter=meter,
            timestamp__gte=start,
            timestamp__lt=end,
            reading_type='interval'
        ).order_by('timestamp'))

        hourly_data = {}
        prev = None
        
        for r in readings:
            hour = r.timestamp.hour
            if hour not in hourly_data:
                hourly_data[hour] = {'gen': Decimal('0'), 'exp': Decimal('0')}
            
            if prev and r.reading_kwh and prev.reading_kwh:
                diff = r.reading_kwh - prev.reading_kwh
                if diff > 0:
                    hourly_data[hour]['gen'] += diff
            
            if prev and r.grid_export_kwh and prev.grid_export_kwh:
                diff = r.grid_export_kwh - prev.grid_export_kwh
                if diff > 0:
                    hourly_data[hour]['exp'] += diff
            
            prev = r

        chart = []
        for i in range(24):
            gen = float(hourly_data.get(i, {}).get('gen', 0))
            exp = float(hourly_data.get(i, {}).get('exp', 0))
            chart.append({
                'label': str(i),
                'generation': round(gen, 2),
                'export': round(exp, 2),
                'self_consumption': round(max(0, gen - exp), 2)
            })

        return {
            'chart': chart,
            'total_generation': round(sum(c['generation'] for c in chart), 2),
            'total_export': round(sum(c['export'] for c in chart), 2),
            'total_self_consumption': round(sum(c['self_consumption'] for c in chart), 2)
        }

    def _get_weekly_data(self, meter, target_date):
        """週次: 日ごとのデータ（7日間）"""
        start = target_date - timedelta(days=target_date.weekday())
        end = start + timedelta(days=7)

        summaries = list(DailySummary.objects.filter(
            meter=meter,
            date__gte=start,
            date__lt=end
        ).order_by('date'))

        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        chart = []
        
        for i in range(7):
            day = start + timedelta(days=i)
            s = next((x for x in summaries if x.date == day), None)
            gen = float(s.generation_kwh or 0) if s else 0
            exp = float(s.export_kwh or 0) if s else 0
            self_c = float(s.self_consumption_kwh or 0) if s else max(0, gen - exp)
            chart.append({
                'label': weekdays[i],
                'generation': round(gen, 2),
                'export': round(exp, 2),
                'self_consumption': round(self_c, 2)
            })

        return {
            'chart': chart,
            'total_generation': round(sum(c['generation'] for c in chart), 2),
            'total_export': round(sum(c['export'] for c in chart), 2),
            'total_self_consumption': round(sum(c['self_consumption'] for c in chart), 2)
        }

    def _get_monthly_data(self, meter, target_date):
        """月次: 日ごとのデータ（1ヶ月）"""
        import calendar
        year, month = target_date.year, target_date.month
        _, days = calendar.monthrange(year, month)
        start = target_date.replace(day=1)

        summaries = list(DailySummary.objects.filter(
            meter=meter,
            date__gte=start,
            date__lt=start + timedelta(days=days)
        ).order_by('date'))

        chart = []
        for i in range(1, days + 1):
            day = start.replace(day=i)
            s = next((x for x in summaries if x.date == day), None)
            gen = float(s.generation_kwh or 0) if s else 0
            exp = float(s.export_kwh or 0) if s else 0
            self_c = float(s.self_consumption_kwh or 0) if s else max(0, gen - exp)
            chart.append({
                'label': str(i),
                'generation': round(gen, 2),
                'export': round(exp, 2),
                'self_consumption': round(self_c, 2)
            })

        return {
            'chart': chart,
            'total_generation': round(sum(c['generation'] for c in chart), 2),
            'total_export': round(sum(c['export'] for c in chart), 2),
            'total_self_consumption': round(sum(c['self_consumption'] for c in chart), 2)
        }

    def _get_yearly_data(self, meter, target_date):
        """年次: 月ごとのデータ（12ヶ月）"""
        year = target_date.year

        summaries = list(MonthlySummary.objects.filter(
            meter=meter,
            year_month__startswith=str(year)
        ).order_by('year_month'))

        chart = []
        for i in range(1, 13):
            ym = f"{year}-{str(i).zfill(2)}"
            s = next((x for x in summaries if x.year_month == ym), None)
            gen = float(s.generation_kwh or 0) if s else 0
            exp = float(s.export_kwh or 0) if s else 0
            self_c = float(s.self_consumption_kwh or 0) if s else max(0, gen - exp)
            chart.append({
                'label': f'{i}月',
                'generation': round(gen, 2),
                'export': round(exp, 2),
                'self_consumption': round(self_c, 2)
            })

        return {
            'chart': chart,
            'total_generation': round(sum(c['generation'] for c in chart), 2),
            'total_export': round(sum(c['export'] for c in chart), 2),
            'total_self_consumption': round(sum(c['self_consumption'] for c in chart), 2)
        }
