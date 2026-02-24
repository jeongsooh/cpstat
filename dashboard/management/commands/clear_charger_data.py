from django.core.management.base import BaseCommand
# 본인의 앱 이름으로 변경하세요 (예: myapp.models)
from dashboard.models import cpstatSum

class Command(BaseCommand):
    help = 'DB에 저장된 모든 충전기 상태 요약 데이터를 삭제합니다.'

    def add_arguments(self, parser):
        # 묻지 않고 바로 삭제하는 옵션 (예: 스케줄러 등에서 자동화할 때 유용)
        parser.add_argument(
            '--noinput',
            '--no-input',
            action='store_true',
            help='사용자 확인 없이 바로 데이터를 삭제합니다.',
        )

    def handle(self, *args, **options):
        # 현재 저장된 데이터 개수 확인
        count = cpstatSum.objects.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("현재 DB에 삭제할 데이터가 없습니다."))
            return

        # --noinput 옵션이 없다면 사용자에게 한 번 더 확인
        if not options['noinput']:
            confirm = input(f"⚠️ 정말로 {count}개의 데이터를 모두 삭제하시겠습니까? (yes/no): ")
            if confirm.lower() not in ['y', 'yes']:
                self.stdout.write(self.style.WARNING("데이터 삭제가 취소되었습니다."))
                return

        try:
            # 전체 데이터 삭제 실행
            cpstatSum.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f"✅ 총 {count}개의 데이터가 성공적으로 삭제되었습니다."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 데이터 삭제 중 오류가 발생했습니다: {e}"))