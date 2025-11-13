import datetime
import time
import os
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from .models import User, Turma, AttendanceRequest, TurmaAluno, Presenca, Graduacao, PlanoAula, ItemPlanoAula, Ranking, PosicaoRanking, Pedido
from .forms import GraduacaoForm
import calendar

# Imports para Relatórios
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from openpyxl import Workbook

# --- VIEWS GERAIS ---

def index(request):
    context = {}
    if not request.user.is_authenticated:
        # Lógica para usuários não autenticados
        students = User.objects.all().filter(group_role='STD', active=True)
        professors = User.objects.all().filter(group_role='PRO', active=True)
        context.update({
            'students': students,
            'professors': professors,
        })
    return render(request, 'academia/index.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            context = {'error': 'Credenciais inválidas ou usuário não encontrado.'}
            return render(request, 'academia/login.html', context)
    else:
        return render(request, 'academia/login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('index')

def solicitar_acesso(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        birthday = request.POST.get('birthday')
        uploaded_photo = request.FILES.get('photo') # Store the uploaded photo temporarily

        if password != password_confirm:
            messages.error(request, 'As senhas não coincidem.')
            return redirect('solicitar_acesso')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Este nome de usuário já está em uso.')
            return redirect('solicitar_acesso')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Este email já está em uso.')
            return redirect('solicitar_acesso')

        # Create the user without the photo first to get an ID
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
            birthday=birthday,
            is_active=False
        )
        
        # If a photo was uploaded, assign it now that the user has an ID
        if uploaded_photo:
            user.photo = uploaded_photo
            user.save() # Save again to save the photo with the correct filename

        messages.success(request, 'Sua solicitação de acesso foi enviada com sucesso! Aguarde a aprovação de um administrador.')
        return redirect('login')

    return render(request, 'academia/solicitar_acesso.html')

@login_required
def dashboard(request):
    # Lógica dos aniversariantes
    selected_month = request.GET.get('month')
    if not selected_month:
        selected_month = datetime.date.today().month
    else:
        try:
            selected_month = int(selected_month)
        except (ValueError, TypeError):
            selected_month = datetime.date.today().month

    aniversariantes = User.objects.filter(birthday__month=selected_month, active=True).order_by('birthday__day')
    
    month_names = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    
    months = [{'number': i + 1, 'name': name} for i, name in enumerate(month_names)]

    base_context = {
        'aniversariantes': aniversariantes,
        'selected_month': selected_month,
        'months': months,
    }

    if request.user.group_role == 'STD':
        presencas_pendentes = AttendanceRequest.objects.filter(student=request.user, status='PEN').count()
        presencas_aprovadas = AttendanceRequest.objects.filter(student=request.user, status='APR').count()
        turmas = TurmaAluno.objects.filter(aluno=request.user)
        context = {
            'presencas_pendentes': presencas_pendentes,
            'presencas_aprovadas': presencas_aprovadas,
            'turmas': turmas,
        }
        context.update(base_context)
        return render(request, 'academia/dashboard_aluno.html', context)
    elif request.user.group_role == 'PRO':
        turmas_count = Turma.objects.filter(professor=request.user, ativa=True).count()
        solicitacoes_presenca = AttendanceRequest.objects.filter(turma__professor=request.user, status='PEN').count()
        alunos_ativos = User.objects.filter(group_role='STD', turmas__professor=request.user, active=True).distinct().count()
        alunos_pendentes = User.objects.filter(group_role='STD', is_active=False).distinct().count()
        pedidos_pendentes = Pedido.objects.filter(aluno__turmas__professor=request.user, status='PEND').distinct().count()
        context = {
            'turmas_count': turmas_count,
            'solicitacoes_presenca': solicitacoes_presenca,
            'alunos_ativos': alunos_ativos,
            'alunos_pendentes': alunos_pendentes,
            'pedidos_pendentes': pedidos_pendentes,
        }
        context.update(base_context)
        return render(request, 'academia/dashboard_professor.html', context)
    elif request.user.group_role == 'ADM':
        total_students = User.objects.filter(group_role='STD', is_active=True).count()
        total_professors = User.objects.filter(group_role='PRO', is_active=True).count()
        total_active_turmas = Turma.objects.filter(ativa=True).count()
        pending_attendance_requests = AttendanceRequest.objects.filter(status='PEN').order_by('-attendance_date')[:5]
        pending_pedidos = Pedido.objects.filter(status='PEND').order_by('-data_solicitacao')[:5]

        # Data for admin dashboard cards (similar to professor dashboard)
        turmas_count = Turma.objects.filter(ativa=True).count()
        solicitacoes_presenca = AttendanceRequest.objects.filter(status='PEN').count()
        alunos_ativos = User.objects.filter(group_role='STD', is_active=True).count()
        alunos_pendentes = User.objects.filter(group_role='STD', is_active=False).count()
        pedidos_pendentes = Pedido.objects.filter(status='PEND').count()

        context = {
            'total_students': total_students,
            'total_professors': total_professors,
            'total_active_turmas': total_active_turmas,
            'pending_attendance_requests': pending_attendance_requests,
            'pending_pedidos': pending_pedidos,
            'turmas_count': turmas_count,
            'solicitacoes_presenca': solicitacoes_presenca,
            'alunos_ativos': alunos_ativos,
            'alunos_pendentes': alunos_pendentes,
            'pedidos_pendentes': pedidos_pendentes,
        }
        context.update(base_context)
        return render(request, 'academia/dashboard_administrador.html', context)
    else:
        return redirect('index')

@login_required
def perfil(request):
    return render(request, 'academia/perfil.html', {'user': request.user})

@login_required
def perfil_editar(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.birthday = request.POST.get('birthday')
        if request.FILES.get('photo'):
            user.photo = request.FILES.get('photo')
        user.save()
        return redirect('perfil')
    return render(request, 'academia/perfil_editar.html', {'user': request.user})

# --- PAINEL DO ALUNO ---

@login_required
def aluno_marcar_presenca(request):
    if request.user.group_role != 'STD':
        raise PermissionDenied("Apenas alunos podem marcar presença.")

    if request.method == 'POST':
        turma_id = request.POST.get('turma_id')
        dates = request.POST.getlist('dates')

        if not turma_id or not dates:
            messages.error(request, 'Turma e pelo menos uma data são obrigatórias.')
            return redirect('aluno_marcar_presenca')

        turma = get_object_or_404(Turma, id=turma_id)

        if not TurmaAluno.objects.filter(aluno=request.user, turma=turma).exists():
            messages.error(request, 'Você não está inscrito nesta turma.')
            return redirect('aluno_marcar_presenca')

        for date_str in dates:
            try:
                attendance_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue

            if not AttendanceRequest.objects.filter(student=request.user, turma=turma, attendance_date=attendance_date).exists():
                AttendanceRequest.objects.create(
                    student=request.user,
                    turma=turma,
                    attendance_date=attendance_date,
                    reason="Solicitação de presença pelo aluno."
                )

        messages.success(request, 'Presenças solicitadas com sucesso!')
        return redirect('aluno_presencas')

    turmas_aluno = TurmaAluno.objects.filter(aluno=request.user, status='APRO').select_related('turma')
    
    context = {
        'turmas_aluno': turmas_aluno,
    }
    return render(request, 'academia/aluno/marcar_presenca.html', context)

@login_required
def aluno_cancelar_presenca(request, presenca_id):
    if request.user.group_role != 'STD':
        raise PermissionDenied("Apenas alunos podem cancelar presenças.")

    attendance_request = get_object_or_404(AttendanceRequest, id=presenca_id, student=request.user)

    # Só pode cancelar se estiver pendente
    if attendance_request.status != 'PEN':
        messages.error(request, 'Só é possível cancelar solicitações pendentes.')
        return redirect('aluno_presencas')

    attendance_request.status = 'CAN'
    attendance_request.save()

    messages.success(request, 'Solicitação de presença cancelada com sucesso.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Cancelado com sucesso.'})

    return redirect('aluno_presencas')

@login_required
def aluno_presencas(request):
    attendance_requests = AttendanceRequest.objects.filter(student=request.user).select_related('turma').order_by('-attendance_date')
    return render(request, 'academia/aluno/presencas.html', {'attendance_requests': attendance_requests})

@login_required
def aluno_graduacoes(request):
    if request.user.group_role != 'STD':
        raise PermissionDenied("Apenas alunos podem visualizar suas graduações.")
    
    graduacoes = Graduacao.objects.filter(aluno=request.user).order_by('-data_graduacao')
    
    # Mark new graduations as notified when the student views them
    Graduacao.objects.filter(aluno=request.user, notified=False).update(notified=True)

    return render(request, 'academia/aluno/graduacoes.html', {'graduacoes': graduacoes})

@login_required
def aluno_relatorios(request):
    # Lógica para gerar relatórios do aluno
    return render(request, 'academia/aluno/relatorios.html')

# --- PAINEL DO PROFESSOR ---

@login_required
def professor_turmas(request):
    if request.user.group_role == 'ADM':
        turmas = Turma.objects.all()
    else:
        turmas = Turma.objects.filter(professor=request.user)
    return render(request, 'academia/professor/turmas.html', {'turmas': turmas})

@login_required
def professor_turma_nova(request):
    # Lógica para criar nova turma
    return render(request, 'academia/professor/turma_form.html')

@login_required
def professor_turma_editar(request, turma_id):
    if request.user.group_role == 'ADM':
        turma = get_object_or_404(Turma, pk=turma_id)
    else:
        turma = get_object_or_404(Turma, pk=turma_id, professor=request.user)
    return render(request, 'academia/professor/turma_form.html', {'turma': turma})

@login_required
def professor_alunos(request):
    alunos = User.objects.filter(group_role='STD').order_by('-is_active')
    return render(request, 'academia/professor/alunos.html', {'alunos': alunos})

@login_required
def professor_aluno_desativar(request, aluno_id):
    aluno = get_object_or_404(User, pk=aluno_id, group_role='STD')
    aluno.active = False
    aluno.save()
    return redirect('professor_alunos')

@login_required
def professor_aluno_ativar(request, aluno_id):
    aluno = get_object_or_404(User, pk=aluno_id)
    aluno.is_active = True
    aluno.save()
    messages.success(request, f'O usuário {aluno.get_full_name()} foi ativado com sucesso.')
    return redirect('professor_alunos')

@login_required
def professor_aluno_definir_tipo(request, aluno_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    user_to_change = get_object_or_404(User, pk=aluno_id, group_role='STD')

    if request.method == 'POST':
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        if request.user.check_password(password):
            if user_type == 'PRO':
                user_to_change.group_role = 'PRO'
                user_to_change.save()
                messages.success(request, f'O usuário {user_to_change.get_full_name()} foi promovido a professor.')
                return redirect('professor_alunos')
            else:
                messages.error(request, 'Ação inválida.')
        else:
            messages.error(request, 'Senha incorreta. A alteração não foi realizada.')

    context = {
        'user_to_change': user_to_change
    }
    return render(request, 'academia/professor/change_user_type.html', context)

@login_required
def professor_presencas(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    if request.user.group_role == 'ADM':
        pending_requests = AttendanceRequest.objects.filter(status='PEN').select_related('student', 'turma').order_by('-attendance_date')
    else:
        pending_requests = AttendanceRequest.objects.filter(turma__professor=request.user, status='PEN').select_related('student', 'turma').order_by('-attendance_date')
    
    context = {
        'pending_requests': pending_requests
    }
    return render(request, 'academia/professor/presencas.html', context)

@login_required
def professor_presenca_aprovar(request, presenca_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    attendance_request = get_object_or_404(AttendanceRequest, id=presenca_id)
    
    if request.user.group_role == 'PRO' and attendance_request.turma.professor != request.user:
        raise PermissionDenied

    attendance_request.status = 'APR'
    attendance_request.processed_by = request.user
    attendance_request.processed_at = timezone.now()
    attendance_request.save()

    messages.success(request, 'Solicitação de presença aprovada.')
    return redirect('professor_presencas')

@login_required
def professor_presenca_rejeitar(request, presenca_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    attendance_request = get_object_or_404(AttendanceRequest, id=presenca_id)

    if request.user.group_role == 'PRO' and attendance_request.turma.professor != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        reason = request.POST.get('rejection_reason', 'Sem motivo especificado.')
        attendance_request.status = 'REJ'
        attendance_request.rejection_reason = reason
        attendance_request.processed_by = request.user
        attendance_request.processed_at = timezone.now()
        attendance_request.save()
        messages.success(request, 'Solicitação de presença rejeitada.')
        return redirect('professor_presencas')

    return redirect('professor_presencas')

@login_required
def professor_attendance_aprovar(request, request_id):
    """Aprova uma solicitação de presença (AttendanceRequest)"""
    if request.method == 'POST':
        attendance_req = get_object_or_404(AttendanceRequest, id=request_id)

        # Verificar permissão
        if request.user.group_role not in ['PRO', 'ADM']:
            raise PermissionDenied
        if request.user.group_role == 'PRO' and attendance_req.turma.professor != request.user:
            raise PermissionDenied

        attendance_req.status = 'APR'
        attendance_req.processed_at = timezone.now()
        attendance_req.processed_by = request.user
        attendance_req.save()

        messages.success(request, f'Solicitação de presença do aluno {attendance_req.student.first_name} aprovada.')
        return redirect('professor_presencas')

    return redirect('professor_presencas')

@login_required
def professor_attendance_rejeitar(request, request_id):
    """Rejeita uma solicitação de presença com motivo"""
    if request.method == 'POST':
        attendance_req = get_object_or_404(AttendanceRequest, id=request_id)

        # Verificar permissão
        if request.user.group_role not in ['PRO', 'ADM']:
            raise PermissionDenied
        if request.user.group_role == 'PRO' and attendance_req.turma.professor != request.user:
            raise PermissionDenied

        rejection_reason = request.POST.get('rejection_reason', '')

        attendance_req.status = 'REJ'
        attendance_req.rejection_reason = rejection_reason
        attendance_req.processed_at = timezone.now()
        attendance_req.processed_by = request.user
        attendance_req.save()

        messages.success(request, f'Solicitação de presença do aluno {attendance_req.student.first_name} rejeitada.')
        return redirect('professor_presencas')

    return redirect('professor_presencas')

@login_required
def professor_graduacoes(request):
    if request.user.group_role == 'ADM':
        alunos = User.objects.filter(group_role='STD')
        graduacoes = Graduacao.objects.all()
    else:
        alunos = User.objects.filter(group_role='STD', turmas__professor=request.user).distinct()
        graduacoes = Graduacao.objects.filter(aluno__in=alunos).distinct()
    
    context = {
        'alunos': alunos,
        'graduacoes': {grad.aluno.id: grad for grad in graduacoes}
    }
    return render(request, 'academia/professor/graduacoes.html', context)

@login_required
def professor_graduacao_editar(request, aluno_id):
    aluno = get_object_or_404(User, id=aluno_id)
    graduacao, created = Graduacao.objects.get_or_create(aluno=aluno)

    if request.method == 'POST':
        form = GraduacaoForm(request.POST, instance=graduacao)
        if form.is_valid():
            form.save()
            messages.success(request, 'Graduação salva com sucesso!')
            return redirect('professor_graduacoes')
    else:
        form = GraduacaoForm(instance=graduacao)

    return render(request, 'academia/professor/graduacao_form.html', {'form': form, 'aluno': aluno})

@login_required
def aluno_graduacoes(request):
    if request.user.group_role != 'STD':
        raise PermissionDenied("Apenas alunos podem visualizar suas graduações.")
    
    graduacoes = Graduacao.objects.filter(aluno=request.user).order_by('-data_graduacao')
    
    # Mark new graduations as notified when the student views them
    Graduacao.objects.filter(aluno=request.user, notified=False).update(notified=True)

    return render(request, 'academia/aluno/graduacoes.html', {'graduacoes': graduacoes})

@login_required
def professor_planos_aula(request):
    if request.user.group_role == 'ADM':
        planos_aula = PlanoAula.objects.all()
    else:
        planos_aula = PlanoAula.objects.filter(professor=request.user)
    return render(request, 'academia/professor/planos_aula.html', {'planos_aula': planos_aula})

@login_required
def professor_plano_aula_novo(request):
    return render(request, 'academia/professor/plano_aula_form.html')

@login_required
def professor_plano_aula_editar(request, plano_id):
    if request.user.group_role == 'ADM':
        plano_aula = get_object_or_404(PlanoAula, pk=plano_id)
    else:
        plano_aula = get_object_or_404(PlanoAula, pk=plano_id, professor=request.user)
    return render(request, 'academia/professor/plano_aula_form.html', {'plano_aula': plano_aula})

@login_required
def professor_rankings(request):
    rankings = Ranking.objects.all()
    return render(request, 'academia/professor/rankings.html', {'rankings': rankings})

@login_required
def professor_ranking_novo(request):
    return render(request, 'academia/professor/ranking_form.html')

@login_required
def professor_pedidos(request):
    if request.user.group_role == 'ADM':
        pedidos = Pedido.objects.all()
    else:
        pedidos = Pedido.objects.filter(aluno__turmas__professor=request.user).distinct()
    return render(request, 'academia/professor/pedidos.html', {'pedidos': pedidos})

@login_required
def professor_pedido_aprovar(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    pedido.status = 'APRO'
    pedido.save()
    return redirect('professor_pedidos')

@login_required
def professor_pedido_rejeitar(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    pedido.status = 'REJE'
    pedido.save()
    return redirect('professor_pedidos')

@login_required
def professor_relatorios(request):
    return render(request, 'academia/professor/relatorios.html')


# --- FUNÇÕES DE VERIFICAÇÃO DE GRUPO ---
def is_student(user):
    return user.is_authenticated and user.group_role == 'STD'

def is_teacher(user):
    return user.is_authenticated and user.group_role == 'PRO'

def is_administrator(user):
    return user.is_authenticated and user.group_role == 'ADM'
