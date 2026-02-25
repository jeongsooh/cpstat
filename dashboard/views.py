import json
import csv
from django.http import HttpResponse
from django.db.models import Sum, F, Q
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView, DeleteView, UpdateView
from .models import cpstatSum
# from .forms import RegisterForm, LoginForm

# # Create your views here.
import json
from django.db.models import Sum, F
from django.views.generic import ListView
from .models import cpstatSum

class cpstatSumList(ListView):
    model = cpstatSum
    template_name = 'cpstatsum_list.html'
    context_object_name = 'cpstatsumList'
    paginate_by = 12

    def get_queryset(self):
        # 1. 상위 5개 사업자 + TOTAL + GRE 찾기
        top_5_qs = cpstatSum.objects.exclude(busiid__in=['TOTAL', 'GRE']).values('busiid').annotate(
            grand_total=Sum(
                F('stat_1_count') + F('stat_2_count') + F('stat_3_count') + 
                F('stat_4_count') + F('stat_5_count') + F('stat_9_count')
            )
        ).order_by('-grand_total')[:5]
        
        # 클래스 변수로 저장하여 get_context_data에서도 사용
        self.target_busiids = [item['busiid'] for item in top_5_qs] + ['TOTAL', 'GRE']

        # 2. 데이터를 최신순으로 가져옵니다.
        qs = cpstatSum.objects.filter(busiid__in=self.target_busiids).order_by('-collected_date', '-hour')

        # 3. 시간(행) 기준으로 피벗 만들기 & 최근 168개 제한
        pivot_dict = {}
        
        for obj in qs:
            time_key = f"{obj.collected_date.strftime('%Y-%m-%d')} {obj.hour:02d}"
            
            # 새로운 시간대가 등장했을 때
            if time_key not in pivot_dict:
                # 168개가 이미 채워졌다면 169번째 데이터부터는 아예 처리하지 않고 종료!
                if len(pivot_dict) >= 168:
                    break 
                
                # 빈 데이터 구조 초기화
                pivot_dict[time_key] = {
                    'collected_date': obj.collected_date,
                    'hour': obj.hour,
                    'busi_data': [{'charge': 0, 'error': 0} for _ in range(len(self.target_busiids))]
                }

            # 충전율/장애율 계산
            total = (obj.stat_1_count + obj.stat_2_count + obj.stat_3_count + 
                     obj.stat_4_count + obj.stat_5_count + obj.stat_9_count)
            
            if total > 0:
                charge_rate = (obj.stat_3_count / total) * 100
                error_rate = ((obj.stat_1_count + obj.stat_4_count + obj.stat_5_count + obj.stat_9_count) / total) * 100
            else:
                charge_rate = 0
                error_rate = 0

            # 데이터를 올바른 사업자 위치(idx)에 삽입
            idx = self.target_busiids.index(obj.busiid)
            pivot_dict[time_key]['busi_data'][idx] = {
                'charge': round(charge_rate, 2),
                'error': round(error_rate, 2)
            }

        # 4. 표와 차트에서 공통으로 쓰기 위해 클래스 변수에 저장해 둠 (DB 중복 호출 방지)
        self.full_table_data = list(pivot_dict.values())
        
        # Pagination 처리를 위해 168개 리스트를 반환 (Django가 이 중 12개씩 잘라서 표에 보여줍니다)
        return self.full_table_data


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        BUSI_MAP = {
            'PL': '플러그링크', 'ME': '환경부', 'EV': '에버온', 'LU': 'LG유플러스',
            'NT': '나이스차저', 'PI': 'GS차지비', 'PW': '파워큐브코리아', 'TOTAL': '전체사업자',
            'GRE': '플러그링크(GRE)',
        }

        # 테이블 컬럼 헤더 생성을 위해 사업자 정보 전달
        target_busi_info = [{'id': b, 'name': BUSI_MAP.get(b, b)} for b in self.target_busiids]
        context['target_busi_info'] = target_busi_info

        # ==========================================
        # 차트용 데이터 가공 (DB 조회 없이 self.full_table_data 재활용)
        # ==========================================
        
        # 차트는 시간이 왼쪽(과거)에서 오른쪽(최신)으로 가야 하므로 데이터를 뒤집어 줍니다.
        chart_raw_data = list(reversed(self.full_table_data))
        
        times = []
        charge_rates = {b: [] for b in self.target_busiids}
        error_rates = {b: [] for b in self.target_busiids}

        # 저장해둔 리스트에서 값을 쏙쏙 뽑아서 차트용 배열로 재조립
        for row in chart_raw_data:
            time_str = f"{row['collected_date'].strftime('%m-%d')} {row['hour']}시"
            times.append(time_str)
            
            for idx, b in enumerate(self.target_busiids):
                charge_rates[b].append(row['busi_data'][idx]['charge'])
                error_rates[b].append(row['busi_data'][idx]['error'])

        chart_data = {
            'labels': times,
            'charge_datasets': [{'label': BUSI_MAP.get(b, b), 'data': charge_rates[b]} for b in self.target_busiids],
            'error_datasets': [{'label': BUSI_MAP.get(b, b), 'data': error_rates[b]} for b in self.target_busiids],
        }
        
        context['chart_data_json'] = json.dumps(chart_data)

        # 페이지네이션 파라미터 유지
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_string'] = query_params.urlencode()

        return context

class cpostatSumList(ListView):
  model = cpstatSum
  template_name='cpostatsum_list.html'
  context_object_name = 'cpostatsumList'
  paginate_by = 12
  queryset = cpstatSum.objects.all()


  def get_queryset(self):
    qs = cpstatSum.objects.all()
    selected_busiid = self.request.GET.get("busiid", "PL")
    qs = qs.filter(busiid=selected_busiid)

    start_date = self.request.GET.get("start_date")
    start_hour = self.request.GET.get("start_hour")
    end_date = self.request.GET.get("end_date")
    end_hour = self.request.GET.get("end_hour")

    if start_date:
      if start_hour:
        # 시작일보다 크거나, 시작일과 같으면서 시간이 크거나 같은 경우
        qs = qs.filter(
          Q(collected_date__gt=start_date) | 
          Q(collected_date=start_date, hour__gte=int(start_hour))
        )
      else:
        qs = qs.filter(collected_date__gte=start_date)

    if end_date:
      if end_hour:
        # 종료일보다 작거나, 종료일과 같으면서 시간이 작거나 같은 경우
        qs = qs.filter(
          Q(collected_date__lt=end_date) | 
          Q(collected_date=end_date, hour__lte=int(end_hour))
        )
      else:
        qs = qs.filter(collected_date__lte=end_date)

    return qs.order_by('-collected_date', '-hour')

  def get_context_data(self, **kwargs):
    context = super(cpostatSumList, self).get_context_data(**kwargs)
    context['selected_busiid'] = self.request.GET.get("busiid", "PL")
    context['start_date'] = self.request.GET.get("start_date", "")
    context['start_hour'] = self.request.GET.get("start_hour", "")
    context['end_date'] = self.request.GET.get("end_date", "")
    context['end_hour'] = self.request.GET.get("end_hour", "")

    BUSI_MAP = {
      'PL': '플러그링크', 'ME': '기후환경부', 'EV': '에버온', 'LU': 'LG유플러스볼트업',
      'NT': '나이스차저', 'PI': 'GS차지비', 'PW': '파워큐브코리아', 'TOTAL': '전체사업자',
      'GRE': '플러그링크(GRE)', # GRE도 매핑 추가 (필요에 따라 이름 조정)
    }
    raw_busiid_list = cpstatSum.objects.values_list('busiid', flat=True).distinct().order_by('busiid')
    context['busiid_list'] = [{'id': b, 'name': BUSI_MAP.get(b, b)} for b in raw_busiid_list]
    context['selected_busi_name'] = BUSI_MAP.get(context['selected_busiid'], context['selected_busiid'])

    # 추가: 현재의 GET 파라미터(검색조건)를 그대로 유지하기 위한 로직
    query_params = self.request.GET.copy()
    # 파라미터 중에 'page'가 있다면 중복을 막기 위해 제거합니다.
    if 'page' in query_params:
      del query_params['page']
    
    # 나머지 검색 조건들을 & 로 이어진 문자열로 변환 (예: busiid=PL&start_date=2026-02-12)
    context['query_string'] = query_params.urlencode()

    return context
  
  # 5. CSV 다운로드 처리 로직
  def get(self, request, *args, **kwargs):
    # 'export' 파라미터가 'csv'인 경우에만 CSV 다운로드 실행
    if request.GET.get('export') == 'csv':
      # 필터링된 데이터셋 가져오기
      queryset = self.get_queryset()
      busiid = request.GET.get("busiid", "PL")

      # CSV 응답 설정 (한글 깨짐 방지를 위해 utf-8-sig 사용)
      response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
      response['Content-Disposition'] = f'attachment; filename="stat_{busiid}.csv"'

      writer = csv.writer(response)
      # 헤더 작성
      writer.writerow(['수집 일자', '시간', '통신이상(1)', '충전대기(2)', '충전중(3)', '운영중지(4)', '점검중(5)', '상태미확인(9)', '합계', '추정충전율(%)', '추정장애율(%)'])

      # 데이터 작성
      for stat in queryset:
          # 모델에 @property 로 charging_ratio와 error_ratio가 있다고 가정
          charging_ratio = f"{stat.charging_ratio:.2f}" if hasattr(stat, 'charging_ratio') else ""
          error_ratio = f"{stat.error_ratio:.2f}" if hasattr(stat, 'error_ratio') else ""

          writer.writerow([
              stat.collected_date.strftime('%Y-%m-%d'),
              f"{stat.hour}시",
              stat.stat_1_count,
              stat.stat_2_count,
              stat.stat_3_count,
              stat.stat_4_count,
              stat.stat_5_count,
              stat.stat_9_count,
              stat.total_count,
              charging_ratio,
              error_ratio
          ])
      return response
      
    # export 파라미터가 없으면 정상적으로 HTML 화면 렌더링
    return super().get(request, *args, **kwargs)
