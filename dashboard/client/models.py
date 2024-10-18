from django.db import models

class DeviceMeasure(models.Model):
    id = models.AutoField(primary_key=True)
    config_id = models.IntegerField(default=None, blank=True, null=True)
    version = models.IntegerField()
    config = models.JSONField()
    pta = models.JSONField()
    upload_date = models.DateTimeField(auto_now_add=True)
    points_count = models.IntegerField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

class DeviceMeasurePoint(models.Model):
    measure = models.ForeignKey(DeviceMeasure, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    battery = models.FloatField()
    integrity = models.FloatField()
    sp02 = models.FloatField()
    bpm = models.FloatField()
    obda = models.FloatField()
    audio_sp1 = models.FloatField()
    audio_sp2 = models.FloatField()
    audio_sp3 = models.FloatField()
    audio_sp4 = models.FloatField()
    audio_sp5 = models.FloatField()
    audio_sp6 = models.FloatField()
    audio_sp7 = models.FloatField()
    audio_sp8 = models.FloatField()
    audio_sp9 = models.FloatField()
    audio_sp10 = models.FloatField()

class DoctorConfigurationParameterName(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

class DoctorConfigurationParameterValue(models.Model):
    id = models.AutoField(primary_key=True)
    param = models.ForeignKey(DoctorConfigurationParameterName, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

class DoctorConfiguration(models.Model):
    config_id = models.IntegerField()
    param = models.ForeignKey(DoctorConfigurationParameterName, on_delete=models.CASCADE)
    value = models.ForeignKey(DoctorConfigurationParameterValue, on_delete=models.CASCADE)
    
class DeviceConfigurationParameterName(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    # Range est un objet du type :
    # {
    #     "type": "int" | "selection"
    #     "min": min_val | null,
    #     "max": max_val | null,
    #     "values": ["value1", "value2", "value3", ...] | null
    # }
    # Si le type est "int", min et max sont obligatoires, values est null
    # Si le type est "selection", values est obligatoire, min et max sont null
    range = models.JSONField()
    quantum = models.FloatField()
    default_value = models.FloatField()

class DeviceConfigurationParameterValue(models.Model):
    id = models.AutoField(primary_key=True)
    param = models.ForeignKey(DeviceConfigurationParameterName, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

class DeviceConfiguration(models.Model):
    config_id = models.IntegerField()
    param = models.ForeignKey(DeviceConfigurationParameterName, on_delete=models.CASCADE)
    value = models.ForeignKey(DeviceConfigurationParameterValue, on_delete=models.CASCADE)

class ConfigurationPairings(models.Model):
    id = models.AutoField(primary_key=True)
    doctor_config_id = models.IntegerField()
    device_config_id = models.IntegerField()


