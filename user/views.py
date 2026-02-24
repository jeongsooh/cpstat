from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView, DeleteView, UpdateView
from user.models import User
from .forms import RegisterForm, LoginForm

# Create your views here.
class UserCreateView(CreateView):
  model = User
  template_name = 'user_register.html'
  fields = ['userid', 'password', 'name', 'email',]
  success_url = '/user'

class UserRegisterView(CreateView):
  model = User
  template_name = 'user_register.html'
  fields = ['userid', 'password', 'name', 'email',]
  success_url = '/'

class UserDeleteView(DeleteView):
    model = User
    template_name='user_confirm_delete.html'
    success_url = '/user'

class UserUpdateView(UpdateView):
  model = User
  template_name='user_update.html'
  fields = ['userid', 'password', 'name', 'email',]
  success_url = '/user'

class UserList(ListView):
  model = User
  template_name='user_list.html'
  context_object_name = 'userList'
#   paginate_by = 2
  queryset = User.objects.all()


  def get_queryset(self):
    queryset = User.objects.all()
    query = self.request.GET.get("q", None)
    if query is not None:
      queryset = queryset.filter(
        Q(userid__icontains=query) |
        Q(name__icontains=query) # |
        # Q(phone__icontains=query)
      )
    return queryset

  def get_context_data(self, **kwargs):
    context = super(UserList, self).get_context_data(**kwargs)
    user_id = self.request.session['user']
    context['loginuser'] = user_id
    return context

class UserDetail(DetailView):
  template_name='user_detail.html'
  queryset = User.objects.all()
  context_object_name = 'user'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    user_id = self.request.session['user']
    context['loginuser'] = user_id
    
    return context

class LoginView(FormView):
  template_name = 'login.html'
  form_class = LoginForm
  success_url = '/'

  def form_valid(self, form):
    self.request.session['user'] = form.user_id

    return super().form_valid(form)


def logout(request):
  if 'user' in request.session:
    del(request.session['user'])

  return redirect('/')

def index(request):
  if request.method == 'POST':
    form = LoginForm(request.POST)
    if form.is_valid():
      request.session['user'] = form.data.get('userid')
      return redirect('dashboard/')
  else:
    form = LoginForm()
  return render(request, 'index.html', {'form': form})
