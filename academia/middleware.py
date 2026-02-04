from .logs import create_log
from .models import Log
from django.urls import resolve

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Processa a requisição antes de chegar à view
        response = self.get_response(request)
        
        # Processa a resposta (após a view ter sido executada)
        # Registramos apenas se o usuário estiver autenticado
        if request.user.is_authenticated:
            self.log_action(request, response)
            
        return response

    def log_action(self, request, response):
        # Ignora requisições para arquivos estáticos ou media, se necessário
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return

        # Tenta resolver o nome da URL para uma descrição mais amigável
        try:
            url_name = resolve(request.path_info).url_name
        except:
            url_name = 'unknown'

        method = request.method
        path = request.path
        status_code = response.status_code
        
        # Define o verbo da ação
        action_verb = 'Acessou'
        if method == 'POST':
            action_verb = 'Enviou dados para'
        elif method == 'DELETE':
            action_verb = 'Deletou em'
        elif method == 'PUT' or method == 'PATCH':
            action_verb = 'Atualizou em'
            
        # Detalhes adicionais para exportação/relatórios baseados na URL ou query params
        extra_info = ""
        if 'export' in request.GET:
            action_verb = 'Exportou dados de'
            extra_info = f" (Formato: {request.GET.get('export')})"
        elif 'relatorio' in path or 'report' in path:
            if method == 'GET':
                action_verb = 'Visualizou relatório em'

        # Monta a mensagem de log
        log_message = f"{action_verb} {path} [{method}]{extra_info} (View: {url_name})"
        
        # Determina o status do log baseado no código de resposta HTTP
        status = 'SUCESSO'
        if status_code >= 400:
            status = 'FALHA'
            log_message += f" - Status Code: {status_code}"

        # Verifica o último log do usuário para evitar duplicatas consecutivas
        try:
            last_log = Log.objects.filter(user=request.user).order_by('-timestamp').first()
            if last_log and last_log.action == log_message and last_log.status == status:
                # Se a ação e o status forem idênticos ao último log, não registra novamente
                return
        except Exception as e:
            # Se houver erro ao verificar o último log, segue para criar o novo (melhor logar duplicado do que não logar)
            print(f"Erro ao verificar último log: {e}")

        # Cria o log
        # Usamos um try-except para garantir que o middleware não quebre a aplicação se o log falhar
        try:
            create_log(request.user, log_message, status=status)
        except Exception as e:
            print(f"Erro ao criar log de auditoria: {e}")
