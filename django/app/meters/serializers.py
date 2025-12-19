from rest_framework import serializers
from .models import Meter, MeterAssignment


class MeterAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeterAssignment
        fields = ['id', 'meter', 'project_id', 'start_date', 'end_date', 'created_at', 'updated_at']


class MeterSerializer(serializers.ModelSerializer):
    assignments = MeterAssignmentSerializer(many=True, read_only=True)
    current_project_id = serializers.SerializerMethodField()

    class Meta:
        model = Meter
        fields = ['id', 'meter_id', 'status', 'registered_at', 'last_received_at', 'is_deleted', 'assignments', 'current_project_id', 'created_at', 'updated_at']

    def get_current_project_id(self, obj):
        assignment = obj.assignments.filter(end_date__isnull=True).first()
        return assignment.project_id if assignment else None