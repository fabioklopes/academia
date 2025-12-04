import datetime
import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from .models import User, Turma, AttendanceRequest, TurmaAluno, Graduacao, PlanoAula, Pedido, Item
from .forms import GraduacaoForm, ItemForm, PedidoForm, TurmaForm, SolicitacaoAcessoForm
import calendar
import openpyxl
from openpyxl.utils import get_column_letter
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import BytesIO
import uuid

# --- VIEWS GERAIS ---

def index(request):
    if request.user.is_authenticated:
        if request.user.is_student():
            return redirect('dashboard')
    
    context = {}
    if not request.user.is_authenticated:
        students = User.objects.filter(group_role='STD', is_active=True)
        professors = User.objects.filter(group_role='PRO', is_active=True)
        context.update({
            'students': students,
            'professors': professors,
        })
    else:
        context.update({
            'presencas_aprovadas': AttendanceRequest.objects.filter(student=request.user, status='APR').count(),
            'presencas_pendentes': AttendanceRequest.objects.filter(student=request.user, status='PEN').count(),
        })
        
    return render(request, 'academia/index.html', context)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            next_url = request.GET.get('next')
            return redirect(next_url) if next_url else redirect('dashboard')
        else:
            context = {'error': 'Credenciais inválidas ou usuário não encontrado.'}
            return render(request, 'academia/login.html', context)
    return render(request, 'academia/login.html')

def logout_view(request):
    auth_logout(request)
    return redirect('index')

def solicitar_acesso(request):
    if request.method == 'POST':
        form = SolicitacaoAcessoForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            email = data['email']
            responsible_email = data.get('responsible_email')
            has_responsible = data.get('has_responsible')

            username = email
            if has_responsible and responsible_email == email:
                # Create a unique username for the dependent
                username = f"{email.split('@')[0]}+{uuid.uuid4().hex[:4]}@{email.split('@')[1]}"

            if User.objects.filter(username=username).exists():
                messages.warning(request, 'Este e-mail já está sendo usado por outro usuário.')
                return render(request, 'academia/solicitar_acesso.html', {'form': form})

            user = User(
                username=username, email=email,
                first_name=data['first_name'], last_name=data['last_name'],
                birthday=data['birthday'], is_active=False
            )
            user.set_password(data['password'])

            if data.get('photo'):
                user.photo = data['photo']

            if has_responsible:
                try:
                    responsible_user = User.objects.get(email=responsible_email, group_role='STD', is_active=True)
                    user.responsible = responsible_user
                except User.DoesNotExist:
                    messages.error(request, f'O e-mail do responsável "{responsible_email}" não foi encontrado ou não é de um aluno ativo.')
                    return render(request, 'academia/solicitar_acesso.html', {'form': form})
            
            user.save()
            messages.success(request, 'Sua solicitação de acesso foi enviada com sucesso! Aguarde a aprovação de um administrador.')
            return redirect('login')
    else:
        form = SolicitacaoAcessoForm()

    return render(request, 'academia/solicitar_acesso.html', {'form': form})

@login_required
def switch_account(request, user_id):
    # Store the original user's ID, whether it's the first switch or a subsequent one.
    original_user_id = request.session.get('original_user_id', request.user.id)

    # The user to switch to must be a dependent of the main account holder.
    dependent_user = get_object_or_404(User, id=user_id, responsible_id=original_user_id)
    
    # Log in as the dependent user. This clears the session.
    auth_login(request, dependent_user, backend='django.contrib.auth.backends.ModelBackend')
    
    # Restore the original user's ID in the new session.
    request.session['original_user_id'] = original_user_id
    
    messages.info(request, f"Você agora está gerenciando a conta de {dependent_user.get_full_name()}.")
    return redirect('perfil')

@login_required
def switch_account_back(request):
    original_user_id = request.session.get('original_user_id')
    if original_user_id:
        original_user = get_object_or_404(User, id=original_user_id)
        
        # Log in as the original user. This clears the session, removing 'original_user_id'.
        auth_login(request, original_user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Você voltou para a sua conta.")
    else:
        messages.warning(request, "Nenhuma conta original encontrada para retornar.")

    return redirect('perfil')

@login_required
def dashboard(request):
    selected_month = request.GET.get('month')
    today = datetime.date.today()
    
    try:
        selected_month = int(selected_month) if selected_month else today.month
    except (ValueError, TypeError):
        selected_month = today.month

    aniversariantes = User.objects.filter(birthday__month=selected_month, is_active=True).order_by('birthday__day')
    
    month_names = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    months = [{'number': i + 1, 'name': name} for i, name in enumerate(month_names)]

    base_context = {
        'aniversariantes': aniversariantes,
        'selected_month': selected_month,
        'months': months,
    }

    if request.user.is_student():
        context = {
            'presencas_pendentes': AttendanceRequest.objects.filter(student=request.user, status='PEN').count(),
            'presencas_aprovadas': AttendanceRequest.objects.filter(student=request.user, status='APR').count(),
            'turmas': TurmaAluno.objects.filter(aluno=request.user),
        }
        context.update(base_context)
        return render(request, 'academia/dashboard_aluno.html', context)
    
    elif request.user.is_professor():
        context = {
            'turmas_count': Turma.objects.filter(professor=request.user, ativa=True).count(),
            'solicitacoes_presenca': AttendanceRequest.objects.filter(turma__professor=request.user, status='PEN').count(),
            'alunos_ativos': User.objects.filter(group_role='STD', turmas__professor=request.user, is_active=True).distinct().count(),
            'alunos_pendentes': User.objects.filter(is_active=False).count(),
            'pedidos_pendentes': Pedido.objects.filter(status='PEND').count(),
        }
        context.update(base_context)
        return render(request, 'academia/dashboard_professor.html', context)

    elif request.user.is_admin():
        context = {
            'total_students': User.objects.filter(group_role='STD', is_active=True).count(),
            'total_professors': User.objects.filter(group_role='PRO', is_active=True).count(),
            'total_active_turmas': Turma.objects.filter(ativa=True).count(),
            'pending_attendance_requests': AttendanceRequest.objects.filter(status='PEN').order_by('-attendance_date')[:5],
            'solicitacoes_presenca': AttendanceRequest.objects.filter(status='PEN').count(),
            'alunos_pendentes': User.objects.filter(is_active=False).count(),
            'pedidos_pendentes': Pedido.objects.filter(status='PEND').count(),
        }
        context.update(base_context)
        return render(request, 'academia/dashboard_administrador.html', context)
        
    return redirect('index')

@login_required
def perfil(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        user = request.user

        if action == 'update_kimono':
            user.height = request.POST.get('height')
            user.weight = request.POST.get('weight')
            user.kimono_size = request.POST.get('kimono_size')
            user.belt_size = request.POST.get('belt_size')
            user.save()
            messages.success(request, 'Informações do kimono atualizadas com sucesso!')
        
        elif action == 'change_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_new_password = request.POST.get('confirm_new_password')

            if not user.check_password(current_password):
                messages.error(request, 'Senha atual incorreta.')
            elif new_password != confirm_new_password:
                messages.error(request, 'As novas senhas não coincidem.')
            else:
                user.set_password(new_password)
                user.save()
                auth_login(request, user)
                messages.success(request, 'Senha alterada com sucesso!')
        
        return redirect('perfil')

    context = {
        'graduacao': Graduacao.objects.filter(aluno=request.user).first(),
        'pedidos': Pedido.objects.filter(aluno=request.user).order_by('-data_solicitacao')
    }
    return render(request, 'academia/perfil.html', context)

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
    return render(request, 'academia/perfil_editar.html')

# --- PAINEL DO ALUNO ---

@login_required
def aluno_marcar_presenca(request):
    if not request.user.is_student():
        raise PermissionDenied

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
                if not AttendanceRequest.objects.filter(student=request.user, turma=turma, attendance_date=attendance_date).exists():
                    AttendanceRequest.objects.create(
                        student=request.user, turma=turma,
                        attendance_date=attendance_date,
                        reason="Solicitação de presença pelo aluno."
                    )
            except ValueError:
                continue

        messages.success(request, 'Presenças solicitadas com sucesso!')
        return redirect('aluno_presencas')

    context = {'turmas_aluno': TurmaAluno.objects.filter(aluno=request.user, status='APRO').select_related('turma')}
    return render(request, 'academia/aluno/marcar_presenca.html', context)

@login_required
def aluno_cancelar_presenca(request, request_id):
    if not request.user.is_student():
        raise PermissionDenied

    attendance_request = get_object_or_404(AttendanceRequest, id=request_id, student=request.user)

    if attendance_request.status != 'PEN':
        messages.error(request, 'Só é possível cancelar solicitações pendentes.')
    else:
        attendance_request.status = 'CAN'
        attendance_request.save()
        messages.success(request, 'Solicitação de presença cancelada com sucesso.')

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': 'Cancelado com sucesso.'})

    return redirect('aluno_presencas')

@login_required
def aluno_presencas(request):
    if not request.user.is_student():
        raise PermissionDenied
    
    AttendanceRequest.objects.filter(student=request.user, status='APR', notified=False).update(notified=True)
    
    attendance_requests = AttendanceRequest.objects.filter(student=request.user).select_related('turma').order_by('-attendance_date')
    return render(request, 'academia/aluno/presencas.html', {'attendance_requests': attendance_requests})

@login_required
def aluno_graduacoes(request):
    if not request.user.is_student():
        raise PermissionDenied
    
    Graduacao.objects.filter(aluno=request.user, notified=False).update(notified=True)
    
    graduacoes = Graduacao.objects.filter(aluno=request.user).order_by('-data_graduacao')
    return render(request, 'academia/aluno/graduacoes.html', {'graduacoes': graduacoes})

@login_required
def aluno_pedidos(request):
    if not request.user.is_student():
        raise PermissionDenied
    pedidos = Pedido.objects.filter(aluno=request.user)
    return render(request, 'academia/aluno/pedidos.html', {'pedidos': pedidos})

@login_required
def aluno_pedido_novo(request):
    if not request.user.is_student():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = PedidoForm(request.POST)
        if form.is_valid():
            pedido = form.save(commit=False)
            item = pedido.item
            
            pedido.aluno = request.user
            pedido.final_value = item.valor * pedido.quantidade if item.valor else None
            pedido.save()
            
            messages.success(request, f'Pedido de "{item.nome}" realizado com sucesso! O item está reservado para você por 15 dias.')
            return redirect('aluno_pedidos')
    else:
        form = PedidoForm()

    itens = Item.objects.filter(quantidade__gt=0)
    item_data = {str(item.id): {'valor': str(item.valor), 'quantidade': item.quantidade} for item in itens}
    
    context = {'form': form, 'item_data_json': json.dumps(item_data)}
    return render(request, 'academia/aluno/pedido_form.html', context)

@login_required
def aluno_pedido_cancelar(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Pedido, id=pedido_id, aluno=request.user)

        if pedido.status == 'PEND':
            item = pedido.item
            item.quantidade += pedido.quantidade
            item.save()

            pedido.status = 'CANC'
            pedido.save()
            messages.success(request, 'Pedido cancelado com sucesso e item devolvido ao estoque.')
        else:
            messages.error(request, 'Apenas pedidos pendentes podem ser cancelados.')

    return redirect('aluno_pedidos')

@login_required
def aluno_relatorios(request):
    if not request.user.is_student():
        raise PermissionDenied
    return render(request, 'academia/aluno/relatorios.html')

@login_required
def gerar_relatorio_aluno(request):
    if not request.user.is_student():
        raise PermissionDenied

    report_type = request.GET.get('report_type')
    date_range = request.GET.get('date_range')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    today = datetime.date.today()
    start_date, end_date = None, None

    if date_range == 'current_month':
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])
    elif date_range == 'custom':
        try:
            if start_date_str:
                start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
            if end_date_str:
                end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Formato de data inválido. Use AAAA-MM-DD.")
            return redirect('perfil')

    context = {
        'report_type': report_type, 'start_date': start_date, 'end_date': end_date,
        'report_data': [], 'report_title': '',
        'no_data_message': 'Nenhum dado encontrado para o período selecionado.'
    }

    if report_type == 'frequencia':
        context['report_title'] = 'Relatório de Frequência de Aulas'
        query = AttendanceRequest.objects.filter(student=request.user, status='APR')
        if start_date: query = query.filter(attendance_date__gte=start_date)
        if end_date: query = query.filter(attendance_date__lte=end_date)
        context['report_data'] = query.order_by('attendance_date').select_related('turma')
        if not context['report_data'].exists():
            context['no_data_message'] = 'Nenhuma presença aprovada encontrada.'

    elif report_type == 'graduacao':
        context['report_title'] = 'Relatório de Progresso de Graduação'
        query = Graduacao.objects.filter(aluno=request.user)
        if start_date: query = query.filter(data_graduacao__gte=start_date)
        if end_date: query = query.filter(data_graduacao__lte=end_date)
        context['report_data'] = query.order_by('data_graduacao')
        if not context['report_data'].exists():
            context['no_data_message'] = 'Nenhum registro de graduação encontrado.'

    else:
        messages.error(request, "Tipo de relatório inválido.")
        return redirect('perfil')

    return render(request, 'academia/aluno/relatorio_detalhe.html', context)

@login_required
def aluno_relatorio_presenca(request):
    if not request.user.is_student():
        raise PermissionDenied

    turmas = Turma.objects.filter(alunos=request.user)
    turma_id = request.GET.get('turma')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    export_format = request.GET.get('export')

    today = datetime.date.today()
    if not start_date_str:
        start_date = today.replace(day=1)
    else:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = today
    else:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    report_data = []
    
    if turma_id and turma_id.isdigit():
        turma_id_int = int(turma_id)
        alunos = User.objects.filter(group_role='STD', is_active=True, turmas__id=turma_id_int)

        aulas_ministradas = AttendanceRequest.objects.filter(
            turma_id=turma_id_int,
            attendance_date__range=[start_date, end_date]
        ).values('attendance_date').distinct().count()

        for aluno in alunos:
            graduacao = Graduacao.objects.filter(aluno=aluno).first()
            
            presencas = AttendanceRequest.objects.filter(
                student=aluno,
                turma_id=turma_id_int,
                status='APR',
                attendance_date__range=[start_date, end_date]
            ).count()
            
            faltas = aulas_ministradas - presencas
            assiduidade = (presencas / aulas_ministradas * 100) if aulas_ministradas > 0 else 0
            
            if assiduidade <= 25:
                mensagem = "INSATISFATÓRIO"
            elif 26 <= assiduidade <= 50:
                mensagem = "REGULAR"
            elif 51 <= assiduidade <= 75:
                mensagem = "SATISFATÓRIO"
            else:
                mensagem = "EXCELENTE"
            
            if graduacao:
                grau_text = f"{graduacao.grau} Grau"
                if graduacao.grau != 1:
                    grau_text += 's'
                faixa_grau_text = f"{graduacao.get_faixa_display()} - {grau_text}"
            else:
                faixa_grau_text = "Nenhuma graduação"

            report_data.append({
                'nome_completo': aluno.get_full_name(),
                'faixa_grau': faixa_grau_text,
                'aulas_ministradas': aulas_ministradas,
                'presencas': presencas,
                'faltas': faltas,
                'assiduidade': f"{assiduidade:.2f}%",
                'mensagem': mensagem,
            })
    else:
        turma_id = None

    if export_format == 'pdf':
        template = get_template('academia/aluno/relatorio_presenca_pdf.html')
        html = template.render({'report_data': report_data})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_presenca.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

    if export_format == 'xlsx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="relatorio_presenca.xlsx"'
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Relatório de Presença'
        
        headers = [
            "Nome Completo", "Faixa e Grau", "Aulas Ministradas", 
            "Presenças", "Faltas", "Assiduidade", "Mensagem"
        ]
        for col_num, header_title in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header_title
            worksheet.column_dimensions[get_column_letter(col_num)].width = 20

        for row_num, data in enumerate(report_data, 2):
            worksheet.cell(row=row_num, column=1, value=data['nome_completo'])
            worksheet.cell(row=row_num, column=2, value=data['faixa_grau'])
            worksheet.cell(row=row_num, column=3, value=data['aulas_ministradas'])
            worksheet.cell(row=row_num, column=4, value=data['presencas'])
            worksheet.cell(row=row_num, column=5, value=data['faltas'])
            worksheet.cell(row=row_num, column=6, value=data['assiduidade'])
            worksheet.cell(row=row_num, column=7, value=data['mensagem'])

        workbook.save(response)
        return response

    context = {
        'turmas': turmas,
        'report_data': report_data,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'turma_id': int(turma_id) if turma_id else None,
    }
    return render(request, 'academia/aluno/relatorio_presenca.html', context)

@login_required
def aluno_relatorio_pedidos(request):
    if not request.user.is_student():
        raise PermissionDenied
    
    pedidos = Pedido.objects.filter(aluno=request.user)
    item_id = request.GET.get('item')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    export_format = request.GET.get('export')

    today = datetime.date.today()
    if not start_date_str:
        start_date = today.replace(day=1)
    else:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = today
    else:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if item_id and item_id.isdigit():
        pedidos = pedidos.filter(item_id=item_id)
    else:
        item_id = None
    
    pedidos = pedidos.filter(data_solicitacao__date__range=[start_date, end_date])

    if export_format == 'pdf':
        template = get_template('academia/aluno/relatorio_pedidos_pdf.html')
        html = template.render({'pedidos': pedidos})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_pedidos.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

    if export_format == 'xlsx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="relatorio_pedidos.xlsx"'
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Relatório de Pedidos'
        
        headers = [
            "Data do pedido", "Nome completo", "Descrição do Produto Solicitado (quantidade)",
            "Valor Unitário", "Total", "Status", "Motivo do Status"
        ]
        for col_num, header_title in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header_title
            worksheet.column_dimensions[get_column_letter(col_num)].width = 25

        for row_num, pedido in enumerate(pedidos, 2):
            worksheet.cell(row=row_num, column=1, value=pedido.data_solicitacao.strftime('%d/%m/%Y %H:%M'))
            worksheet.cell(row=row_num, column=2, value=pedido.aluno.get_full_name())
            worksheet.cell(row=row_num, column=3, value=f"{pedido.item.nome} ({pedido.quantidade})")
            worksheet.cell(row=row_num, column=4, value=pedido.item.valor)
            worksheet.cell(row=row_num, column=5, value=pedido.final_value)
            worksheet.cell(row=row_num, column=6, value=pedido.get_status_display())
            worksheet.cell(row=row_num, column=7, value=pedido.rejection_reason or pedido.cancellation_reason or "-")

        workbook.save(response)
        return response

    context = {
        'pedidos': pedidos,
        'itens': Item.objects.all(),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'item_id': int(item_id) if item_id else None,
    }
    return render(request, 'academia/aluno/relatorio_pedidos.html', context)

# --- PAINEL DO PROFESSOR ---

@login_required
def professor_turmas(request):
    turmas = Turma.objects.all() if request.user.is_admin() else Turma.objects.filter(professor=request.user)
    return render(request, 'academia/professor/turmas.html', {'turmas': turmas})

@login_required
def professor_turma_nova(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            turma = form.save(commit=False)
            turma.professor = request.user
            turma.save()
            messages.success(request, f'Turma "{turma.nome}" criada com sucesso!')
            return redirect('professor_turmas')
    else:
        form = TurmaForm()
    
    return render(request, 'academia/professor/turma_form.html', {'form': form})

@login_required
def professor_turma_editar(request, turma_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    turma = get_object_or_404(Turma, pk=turma_id)
    if not request.user.is_admin() and turma.professor != request.user:
        raise PermissionDenied

    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            form.save()
            messages.success(request, f'Turma "{turma.nome}" atualizada com sucesso!')
            return redirect('professor_turmas')
    else:
        form = TurmaForm(instance=turma)
    
    return render(request, 'academia/professor/turma_form.html', {'form': form, 'turma': turma})

@login_required
def professor_turma_alunos(request, turma_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    turma = get_object_or_404(Turma, pk=turma_id)
    if not request.user.is_admin() and turma.professor != request.user:
        raise PermissionDenied
    
    alunos_na_turma_ids = TurmaAluno.objects.filter(turma=turma, status='APRO').values_list('aluno_id', flat=True)
    
    context = {
        'turma': turma,
        'alunos_turma': TurmaAluno.objects.filter(id__in=alunos_na_turma_ids).select_related('aluno'),
        'alunos_disponiveis': User.objects.filter(group_role='STD', is_active=True).exclude(id__in=alunos_na_turma_ids).order_by('first_name', 'last_name'),
    }
    return render(request, 'academia/professor/turma_alunos.html', context)

@login_required
def professor_turma_adicionar_aluno(request, turma_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    turma = get_object_or_404(Turma, pk=turma_id)
    if not request.user.is_admin() and turma.professor != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        alunos_ids = request.POST.getlist('alunos')
        if not alunos_ids:
            messages.error(request, 'Selecione pelo menos um aluno.')
        else:
            count = 0
            for aluno_id in alunos_ids:
                aluno = get_object_or_404(User, pk=aluno_id, group_role='STD')
                if not TurmaAluno.objects.filter(turma=turma, aluno=aluno).exists():
                    TurmaAluno.objects.create(turma=turma, aluno=aluno, status='APRO', data_aprovacao=timezone.now())
                    count += 1
            
            if count > 0:
                messages.success(request, f'{count} aluno(s) adicionado(s) à turma "{turma.nome}".')
            else:
                messages.warning(request, 'Nenhum aluno novo adicionado.')
        
    return redirect('professor_turma_alunos', turma_id=turma_id)

@login_required
def professor_turma_remover_aluno(request, turma_id, aluno_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    turma = get_object_or_404(Turma, pk=turma_id)
    if not request.user.is_admin() and turma.professor != request.user:
        raise PermissionDenied
    
    turma_aluno = get_object_or_404(TurmaAluno, turma=turma, aluno_id=aluno_id)
    aluno_nome = turma_aluno.aluno.get_full_name()
    turma_aluno.delete()
    
    messages.success(request, f'Aluno "{aluno_nome}" removido da turma "{turma.nome}".')
    return redirect('professor_turma_alunos', turma_id=turma_id)

@login_required
def professor_alunos(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    alunos = User.objects.filter(group_role='STD').order_by('first_name')
    return render(request, 'academia/professor/alunos.html', {'alunos': alunos})

@login_required
def professor_aluno_desativar(request, aluno_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    aluno = get_object_or_404(User, pk=aluno_id, group_role='STD')
    aluno.is_active = False
    aluno.save()
    messages.success(request, f'O usuário {aluno.get_full_name()} foi desativado.')
    return redirect('professor_alunos')

@login_required
def professor_aluno_ativar(request, aluno_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    aluno = get_object_or_404(User, pk=aluno_id)
    aluno.is_active = True
    aluno.save()
    messages.success(request, f'O usuário {aluno.get_full_name()} foi ativado.')
    return redirect('professor_alunos')

@login_required
def professor_aluno_definir_tipo(request, aluno_id):
    if not request.user.is_admin():
        raise PermissionDenied

    user_to_change = get_object_or_404(User, pk=aluno_id)

    if request.method == 'POST':
        password = request.POST.get('password')
        user_type = request.POST.get('user_type')

        if not request.user.check_password(password):
            messages.error(request, 'Senha incorreta.')
        elif user_type not in ['STD', 'PRO', 'ADM']:
            messages.error(request, 'Tipo de usuário inválido.')
        else:
            user_to_change.group_role = user_type
            user_to_change.save()
            messages.success(request, f'O tipo de usuário de {user_to_change.get_full_name()} foi alterado.')
            return redirect('professor_alunos')

    return render(request, 'academia/professor/change_user_type.html', {'user_to_change': user_to_change})

@login_required
def tamanhos_medidas(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    students = User.objects.filter(group_role='STD').order_by('first_name', 'last_name')
    today = datetime.date.today()
    student_data = [{
        'user': student,
        'age': today.year - student.birthday.year - ((today.month, today.day) < (student.birthday.month, student.birthday.day)) if student.birthday else None
    } for student in students]

    return render(request, 'academia/professor/tamanhos_medidas.html', {'student_data': student_data})

@login_required
def professor_presencas(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    query = AttendanceRequest.objects.filter(status='PEN')
    if request.user.is_professor():
        query = query.filter(turma__professor=request.user)
    
    pending_requests = query.select_related('student', 'turma').order_by('-attendance_date')
    return render(request, 'academia/professor/presencas.html', {'pending_requests': pending_requests})

@login_required
def professor_presenca_aprovar(request, request_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    attendance_request = get_object_or_404(AttendanceRequest, id=request_id)
    
    if request.user.is_professor() and attendance_request.turma.professor != request.user:
        raise PermissionDenied

    attendance_request.status = 'APR'
    attendance_request.processed_by = request.user
    attendance_request.processed_at = timezone.now()
    attendance_request.save()

    messages.success(request, 'Solicitação de presença aprovada.')
    return redirect('professor_presencas')

@login_required
def professor_presenca_rejeitar(request, request_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    attendance_request = get_object_or_404(AttendanceRequest, id=request_id)

    if request.user.is_professor() and attendance_request.turma.professor != request.user:
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

@login_required
def professor_graduacoes(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    if request.user.is_admin():
        alunos = User.objects.filter(group_role='STD')
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
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
        
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
def professor_planos_aula(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    planos_aula = PlanoAula.objects.all() if request.user.is_admin() else PlanoAula.objects.filter(professor=request.user)
    return render(request, 'academia/professor/planos_aula.html', {'planos_aula': planos_aula})

@login_required
def professor_plano_aula_novo(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    return render(request, 'academia/professor/plano_aula_form.html')

@login_required
def professor_plano_aula_editar(request, plano_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    plano_aula = get_object_or_404(PlanoAula, pk=plano_id)
    if not request.user.is_admin() and plano_aula.professor != request.user:
        raise PermissionDenied
    return render(request, 'academia/professor/plano_aula_form.html', {'plano_aula': plano_aula})

@login_required
def professor_rankings(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    rankings = Ranking.objects.all()
    return render(request, 'academia/professor/rankings.html', {'rankings': rankings})

@login_required
def professor_ranking_novo(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    return render(request, 'academia/professor/ranking_form.html')

@login_required
def professor_pedidos(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    if request.user.is_admin():
        pedidos = Pedido.objects.all()
    else:
        pedidos = Pedido.objects.filter(item__isnull=False, aluno__turmas__professor=request.user).distinct()

    return render(request, 'academia/professor/pedidos.html', {'pedidos': pedidos})

@login_required
def professor_pedido_aprovar(request, pedido_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        pedido.status = 'APRO'
        pedido.aprovado_por = request.user
        pedido.data_aprovacao = timezone.now()
        pedido.save()
        messages.success(request, 'Pedido atendido com sucesso!')
    
    return redirect('professor_pedidos')

@login_required
def professor_pedido_rejeitar(request, pedido_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        if pedido.status == 'PEND':
            item = pedido.item
            item.quantidade += pedido.quantidade
            item.save()

        pedido.status = 'REJE'
        pedido.rejection_reason = request.POST.get('rejection_reason', 'Sem motivo especificado.')
        pedido.save()
        messages.success(request, 'Pedido rejeitado e estoque atualizado.')

    return redirect('professor_pedidos')

@login_required
def professor_pedido_cancelar(request, pedido_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        pedido.status = 'CANC'
        pedido.cancellation_reason = request.POST.get('cancellation_reason', 'Sem motivo especificado.')
        pedido.save()
        messages.success(request, 'Pedido cancelado com sucesso!')

    return redirect('professor_pedidos')

@login_required
def professor_pedido_entregar(request, pedido_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        if pedido.item.quantidade is not None:
            if pedido.quantidade > pedido.item.quantidade:
                messages.error(request, 'Não há estoque suficiente para entregar este pedido.')
                return redirect('professor_pedidos')
            pedido.item.quantidade -= pedido.quantidade
            pedido.item.save()
        
        if final_value := request.POST.get('final_value'):
            pedido.final_value = final_value
        
        pedido.status = 'ENTR'
        pedido.save()
        messages.success(request, 'Pedido marcado como entregue!')

    return redirect('professor_pedidos')

@login_required
def professor_pedido_finalizar(request, pedido_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if request.method == 'POST':
        pedido.status = 'FINA'
        pedido.save()
        messages.success(request, 'Pedido finalizado com sucesso!')

    return redirect('professor_pedidos')

@login_required
def professor_itens(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    return render(request, 'academia/professor/itens.html', {'itens': Item.objects.all()})

@login_required
def professor_item_novo(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item criado com sucesso!')
            return redirect('professor_itens')
    else:
        form = ItemForm()
    return render(request, 'academia/professor/item_form.html', {'form': form})

@login_required
def professor_item_editar(request, item_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item atualizado com sucesso!')
            return redirect('professor_itens')
    else:
        form = ItemForm(instance=item)
    return render(request, 'academia/professor/item_form.html', {'form': form})

@login_required
def professor_item_deletar(request, item_id):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    item = get_object_or_404(Item, pk=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deletado com sucesso!')
        return redirect('professor_itens')
    return render(request, 'academia/professor/item_confirm_delete.html', {'item': item})

@login_required
def professor_relatorios(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    return render(request, 'academia/professor/relatorios.html')

@login_required
def relatorio_pedidos(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied
    
    pedidos = Pedido.objects.all()
    aluno_id = request.GET.get('aluno')
    item_id = request.GET.get('item')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    export_format = request.GET.get('export')

    today = datetime.date.today()
    if not start_date_str:
        start_date = today.replace(day=1)
    else:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = today
    else:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    if aluno_id and aluno_id.isdigit():
        pedidos = pedidos.filter(aluno_id=aluno_id)
    else:
        aluno_id = None

    if item_id and item_id.isdigit():
        pedidos = pedidos.filter(item_id=item_id)
    else:
        item_id = None
    
    pedidos = pedidos.filter(data_solicitacao__date__range=[start_date, end_date])

    if export_format == 'pdf':
        template = get_template('academia/professor/relatorio_pedidos_pdf.html')
        html = template.render({'pedidos': pedidos})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_pedidos.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

    if export_format == 'xlsx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="relatorio_pedidos.xlsx"'
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Relatório de Pedidos'
        
        headers = [
            "Data do pedido", "Nome completo", "Descrição do Produto Solicitado (quantidade)",
            "Valor Unitário", "Total", "Status", "Motivo do Status"
        ]
        for col_num, header_title in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header_title
            worksheet.column_dimensions[get_column_letter(col_num)].width = 25

        for row_num, pedido in enumerate(pedidos, 2):
            worksheet.cell(row=row_num, column=1, value=pedido.data_solicitacao.strftime('%d/%m/%Y %H:%M'))
            worksheet.cell(row=row_num, column=2, value=pedido.aluno.get_full_name())
            worksheet.cell(row=row_num, column=3, value=f"{pedido.item.nome} ({pedido.quantidade})")
            worksheet.cell(row=row_num, column=4, value=pedido.item.valor)
            worksheet.cell(row=row_num, column=5, value=pedido.final_value)
            worksheet.cell(row=row_num, column=6, value=pedido.get_status_display())
            worksheet.cell(row=row_num, column=7, value=pedido.rejection_reason or pedido.cancellation_reason or "-")

        workbook.save(response)
        return response

    context = {
        'pedidos': pedidos,
        'alunos': User.objects.filter(group_role='STD'),
        'itens': Item.objects.all(),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'aluno_id': int(aluno_id) if aluno_id else None,
        'item_id': int(item_id) if item_id else None,
    }
    return render(request, 'academia/professor/relatorio_pedidos.html', context)

@login_required
def relatorio_presenca(request):
    if not request.user.is_professor_or_admin():
        raise PermissionDenied

    turmas = Turma.objects.all() if request.user.is_admin() else Turma.objects.filter(professor=request.user)
    turma_id = request.GET.get('turma')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    export_format = request.GET.get('export')

    today = datetime.date.today()
    if not start_date_str:
        start_date = today.replace(day=1)
    else:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()

    if not end_date_str:
        end_date = today
    else:
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()

    report_data = []
    
    if turma_id and turma_id.isdigit():
        turma_id_int = int(turma_id)
        alunos = User.objects.filter(group_role='STD', is_active=True, turmas__id=turma_id_int)

        aulas_ministradas = AttendanceRequest.objects.filter(
            turma_id=turma_id_int,
            attendance_date__range=[start_date, end_date]
        ).values('attendance_date').distinct().count()

        for aluno in alunos:
            graduacao = Graduacao.objects.filter(aluno=aluno).first()
            
            presencas = AttendanceRequest.objects.filter(
                student=aluno,
                turma_id=turma_id_int,
                status='APR',
                attendance_date__range=[start_date, end_date]
            ).count()
            
            faltas = aulas_ministradas - presencas
            assiduidade = (presencas / aulas_ministradas * 100) if aulas_ministradas > 0 else 0
            
            if assiduidade <= 25:
                mensagem = "INSATISFATÓRIO"
            elif 26 <= assiduidade <= 50:
                mensagem = "REGULAR"
            elif 51 <= assiduidade <= 75:
                mensagem = "SATISFATÓRIO"
            else:
                mensagem = "EXCELENTE"
            
            if graduacao:
                grau_text = f"{graduacao.grau} Grau"
                if graduacao.grau != 1:
                    grau_text += 's'
                faixa_grau_text = f"{graduacao.get_faixa_display()} - {grau_text}"
            else:
                faixa_grau_text = "Nenhuma graduação"

            report_data.append({
                'nome_completo': aluno.get_full_name(),
                'faixa_grau': faixa_grau_text,
                'aulas_ministradas': aulas_ministradas,
                'presencas': presencas,
                'faltas': faltas,
                'assiduidade': f"{assiduidade:.2f}%",
                'mensagem': mensagem,
            })
    else:
        turma_id = None

    if export_format == 'pdf':
        template = get_template('academia/professor/relatorio_presenca_pdf.html')
        html = template.render({'report_data': report_data})
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_presenca.pdf"'
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')
        return response

    if export_format == 'xlsx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="relatorio_presenca.xlsx"'
        
        workbook = openpyxl.Workbook()
        worksheet = workbook.active
        worksheet.title = 'Relatório de Presença'
        
        headers = [
            "Nome Completo", "Faixa e Grau", "Aulas Ministradas", 
            "Presenças", "Faltas", "Assiduidade", "Mensagem"
        ]
        for col_num, header_title in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col_num)
            cell.value = header_title
            worksheet.column_dimensions[get_column_letter(col_num)].width = 20

        for row_num, data in enumerate(report_data, 2):
            worksheet.cell(row=row_num, column=1, value=data['nome_completo'])
            worksheet.cell(row=row_num, column=2, value=data['faixa_grau'])
            worksheet.cell(row=row_num, column=3, value=data['aulas_ministradas'])
            worksheet.cell(row=row_num, column=4, value=data['presencas'])
            worksheet.cell(row=row_num, column=5, value=data['faltas'])
            worksheet.cell(row=row_num, column=6, value=data['assiduidade'])
            worksheet.cell(row=row_num, column=7, value=data['mensagem'])

        workbook.save(response)
        return response

    context = {
        'turmas': turmas,
        'report_data': report_data,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'turma_id': int(turma_id) if turma_id else None,
    }
    return render(request, 'academia/professor/relatorio_presenca.html', context)
