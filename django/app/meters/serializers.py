from rest_framework import serializers
from .models import Meter, MeterAssignment


class MeterAssignmentSerializer(serializers.ModelSerializer):
    zone_display = serializers.CharField(read_only=True)

    class Meta:
        model = MeterAssignment
        fields = [
            'id', 'project_id', 'project_name',
            'zone', 'zone_display', 'base_billing_day',
            'start_date', 'end_date', 'synced_at', 'created_at'
        ]


class MeterSerializer(serializers.ModelSerializer):
    current_project_id = serializers.SerializerMethodField()
    current_project_name = serializers.SerializerMethodField()
    current_zone_display = serializers.SerializerMethodField()
    setup_status = serializers.CharField(read_only=True)
    has_key = serializers.SerializerMethodField()

    class Meta:
        model = Meter
        fields = [
            'id', 'meter_id', 'status',
            'b_route_enabled', 'b_route_id', 'b_route_password',
            'installed_at', 'registered_at', 'last_received_at',
            'current_project_id', 'current_project_name', 'current_zone_display',
            'setup_status', 'has_key',
            'created_at', 'updated_at'
        ]

    def get_current_project_id(self, obj):
        assignment = obj.current_assignment
        return assignment.project_id if assignment else None

    def get_current_project_name(self, obj):
        assignment = obj.current_assignment
        return assignment.project_name if assignment else None

    def get_current_zone_display(self, obj):
        assignment = obj.current_assignment
        return assignment.zone_display if assignment else None

    def get_has_key(self, obj):
        return hasattr(obj, 'key')

class MeterDetailSerializer(MeterSerializer):
    assignments = MeterAssignmentSerializer(many=True, read_only=True)
    current_assignment = MeterAssignmentSerializer(read_only=True)

    class Meta(MeterSerializer.Meta):
        fields = MeterSerializer.Meta.fields + ['assignments', 'current_assignment', 'is_deleted']