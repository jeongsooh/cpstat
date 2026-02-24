from django.db import models

class cpstatSum(models.Model):
    # 시간 정보
    collected_date = models.DateField(verbose_name="수집 일자")
    hour = models.IntegerField(verbose_name="수집 시간(시)")
    
    # 사업자 정보
    busiid = models.CharField(max_length=50, verbose_name="사업자 ID")
    
    # 상태별 개수 (기본값 0)
    stat_1_count = models.IntegerField(default=0, verbose_name="통신이상(1)")
    stat_2_count = models.IntegerField(default=0, verbose_name="충전대기(2)")
    stat_3_count = models.IntegerField(default=0, verbose_name="충전중(3)")
    stat_4_count = models.IntegerField(default=0, verbose_name="운영중지(4)")
    stat_5_count = models.IntegerField(default=0, verbose_name="점검중(5)")
    stat_9_count = models.IntegerField(default=0, verbose_name="상태미확인(9)")

    class Meta:
        # 특정 날짜, 시간의 동일한 사업자 데이터는 1개만 존재해야 함
        unique_together = ('collected_date', 'hour', 'busiid')
        verbose_name = "시간별 충전기 상태 요약"
        verbose_name_plural = "시간별 충전기 상태 요약 목록"

    def __str__(self):
        return f"[{self.collected_date} {self.hour}시] {self.busiid} 통계"

    # 전체 충전기 대수를 계산하는 속성 (웹에서 유용하게 쓰일 수 있습니다)
    @property
    def total_count(self):
        return (self.stat_1_count + self.stat_2_count + self.stat_3_count + 
                self.stat_4_count + self.stat_5_count + self.stat_9_count)
    @property
    def charging_ratio(self):
        if self.total_count == 0:
            return 0
        # 퍼센트로 보여주려면 100을 곱합니다. 단순히 소수점 비율만 필요하면 100을 빼세요.
        return (self.stat_3_count / self.total_count) * 100
    @property
    def error_ratio(self):
        if self.total_count == 0:
            return 0
        # 퍼센트로 보여주려면 100을 곱합니다. 단순히 소수점 비율만 필요하면 100을 빼세요.
        return (self.stat_1_count + self.stat_4_count + self.stat_5_count + self.stat_9_count) / self.total_count * 100

