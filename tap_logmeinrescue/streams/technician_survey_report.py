from tap_logmeinrescue.streams.base import BaseLogMeInRescueReportStream


class TechnicianSurveyReportStream(BaseLogMeInRescueReportStream):
    TABLE = 'technician_survey_report'
    KEY_PROPERTIES = ['session_id']
    API_METHOD = 'GET'
    REPORT_AREA = 8
    REQUIRES = ['technicians']
