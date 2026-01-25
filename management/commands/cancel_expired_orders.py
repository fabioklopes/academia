from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from academia.models import Pedido

class Command(BaseCommand):
    help = 'Cancela pedidos pendentes que expiraram (mais de 15 dias).'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Iniciando verificação de pedidos expirados...'))
        
        # Define o limite de tempo (15 dias atrás)
        expiration_limit = timezone.now() - timedelta(days=15)
        
        # Filtra pedidos pendentes que foram criados antes do limite de tempo
        expired_orders = Pedido.objects.filter(
            status='PEND',
            data_solicitacao__lt=expiration_limit
        )
        
        if not expired_orders.exists():
            self.stdout.write(self.style.SUCCESS('Nenhum pedido expirado encontrado.'))
            return

        count = 0
        for pedido in expired_orders:
            item = pedido.item
            quantidade_reservada = pedido.quantidade
            
            # Devolve a quantidade ao estoque
            item.quantidade += quantidade_reservada
            item.save()
            
            # Atualiza o status do pedido
            pedido.status = 'CANC'
            pedido.cancellation_reason = 'Expirado tempo para atendimento'
            pedido.save()
            
            count += 1
            self.stdout.write(f'Pedido #{pedido.id} para "{item.nome}" cancelado. {quantidade_reservada} unidade(s) devolvida(s) ao estoque.')
            
        self.stdout.write(self.style.SUCCESS(f'Operação concluída. {count} pedido(s) expirado(s) foram cancelados.'))
