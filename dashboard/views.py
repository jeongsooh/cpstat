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

class cpstatSumList(ListView):
  model = cpstatSum
  template_name='cpstatsum_list.html'
  context_object_name = 'cpstatsumList'
  paginate_by = 12
  queryset = cpstatSum.objects.all()


  def get_queryset(self):
    selected_busiid = self.request.GET.get("busiid", "TOTAL")
    queryset = cpstatSum.objects.filter(busiid=selected_busiid).order_by('-collected_date', '-hour')

    return queryset

  def get_context_data(self, **kwargs):
    context = super(cpstatSumList, self).get_context_data(**kwargs)
    selected_busiid = self.request.GET.get("busiid", "TOTAL")

    BUSI_MAP = {
      'PL': '플러그링크', 'ME': '기후환경부', 'EV': '에버온', 'LU': 'LG유플러스볼트업',
      'NT': '나이스차저', 'PI': 'GS차지비', 'PW': '파워큐브코리아', 'TOTAL': '전체사업자',
      'GRE': '플러그링크(GRE)', # GRE도 매핑 추가 (필요에 따라 이름 조정)
    }
    raw_busiid_list = cpstatSum.objects.values_list('busiid', flat=True).distinct().order_by('busiid')
        
    # 3. HTML 템플릿에서 쓰기 좋게 [{'id': 'PL', 'name': '플러그링크'}, ...] 형태로 가공
    formatted_busiid_list = []
    for b_id in raw_busiid_list:
        formatted_busiid_list.append({
            'id': b_id,
            'name': BUSI_MAP.get(b_id, b_id) # 딕셔너리에 없으면 그냥 ID(예: 'XX')를 출력
        })

    context['selected_busiid'] = selected_busiid
    context['busiid_list'] = formatted_busiid_list
    # 화면 제목용으로 현재 선택된 사업자의 한글 이름도 넘겨줍니다.
    context['selected_busi_name'] = BUSI_MAP.get(selected_busiid, selected_busiid)

    # ==========================================
    # [추가] 차트용 데이터 가공 로직
    # ==========================================
    
    # 1. 상위 5개 사업자 찾기 (TOTAL, GRE 제외)
    top_5_qs = cpstatSum.objects.exclude(busiid__in=['TOTAL', 'GRE']).values('busiid').annotate(
        grand_total=Sum(
            F('stat_1_count') + F('stat_2_count') + F('stat_3_count') + 
            F('stat_4_count') + F('stat_5_count') + F('stat_9_count')
        )
    ).order_by('-grand_total')[:5]
    
    # 차트에 표시할 대상 사업자 리스트 (Top 5 + TOTAL + GRE)
    target_busiids = [item['busiid'] for item in top_5_qs] + ['TOTAL', 'GRE']

    # 2. 대상 사업자들의 데이터 모두 가져오기 (시간 오름차순 정렬)
    chart_data_qs = cpstatSum.objects.filter(busiid__in=target_busiids).order_by('collected_date', 'hour')

    # 3. 데이터 가공 (시간별로 정렬)
    times = [] # x축 라벨 (예: 02-09 15시)
    for obj in chart_data_qs:
        time_str = f"{obj.collected_date.strftime('%m-%d')} {obj.hour}시"
        if time_str not in times:
            times.append(time_str)

    # 사업자별로 충전율, 장애율 데이터를 담을 딕셔너리 초기화
    charge_rates = {b: [0] * len(times) for b in target_busiids}
    error_rates = {b: [0] * len(times) for b in target_busiids}

    # 데이터 채우기
    for obj in chart_data_qs:
        time_str = f"{obj.collected_date.strftime('%m-%d')} {obj.hour}시"
        idx = times.index(time_str)
        b = obj.busiid
        
        total = (obj.stat_1_count + obj.stat_2_count + obj.stat_3_count + 
                  obj.stat_4_count + obj.stat_5_count + obj.stat_9_count)
        
        if total > 0:
            # 충전율 (충전중 / 전체)
            charge_rate = (obj.stat_3_count / total) * 100
            # 장애율 ((통신이상 + 상태미확인) / 전체) - 필요시 점검중(5) 포함 가능
            error_rate = ((obj.stat_1_count + obj.stat_4_count + obj.stat_5_count + obj.stat_9_count) / total) * 100
        else:
            charge_rate = 0
            error_rate = 0
            
        charge_rates[b][idx] = round(charge_rate, 2)
        error_rates[b][idx] = round(error_rate, 2)

    # 4. JSON 변환을 위해 구조화
    chart_data = {
        'labels': times,
        'charge_datasets': [{'label': b, 'data': charge_rates[b]} for b in target_busiids],
        'error_datasets': [{'label': b, 'data': error_rates[b]} for b in target_busiids],
    }

    # context에 담아서 전달 (JSON 문자열로 변환)
    context['chart_data_json'] = json.dumps(chart_data)

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
