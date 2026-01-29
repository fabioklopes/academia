from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
from io import StringIO

from .models import User, Item, Pedido
from .forms import PedidoForm

# Dica: Rode os testes com o comando: python manage.py test academia

class ModelTests(TestCase):
    """
    Testes para os Modelos da aplicação.
    """
    def test_create_item_and_str_representation(self):
        """Testa a criação de um Item e se o método __str__ retorna o nome."""
        item = Item.objects.create(nome="Kimono Azul", tipo="KIMONO", valor=350.00, quantidade=10)
        self.assertEqual(str(item), "Kimono Azul")
        self.assertEqual(item.quantidade, 10)

class FormTests(TestCase):
    """
    Testes para os Formulários.
    """
    def setUp(self):
        """Configuração inicial para os testes de formulário."""
        self.item = Item.objects.create(nome="Faixa Roxa", tipo="FAIXA", valor=50.00, quantidade=5)

    def test_pedido_form_valid(self):
        """Testa se o PedidoForm é válido com dados corretos."""
        form_data = {'item': self.item.id, 'quantidade': 2}
        form = PedidoForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_pedido_form_invalid_quantity_too_high(self):
        """Testa se o PedidoForm é inválido se a quantidade for maior que o estoque."""
        form_data = {'item': self.item.id, 'quantidade': 10} # Estoque é 5
        form = PedidoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('quantidade', form.errors)
        self.assertEqual(form.errors['quantidade'][0], "A quantidade solicitada (10) excede o estoque disponível (5).")

    def test_pedido_form_invalid_quantity_zero(self):
        """Testa se o PedidoForm é inválido se a quantidade for zero ou menor."""
        form_data = {'item': self.item.id, 'quantidade': 0}
        form = PedidoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('quantidade', form.errors)

class ViewTests(TestCase):
    """
    Testes para as Views.
    """
    def setUp(self):
        """Configuração inicial para os testes de view."""
        self.client = Client()
        self.student_user = User.objects.create_user(username='aluno', password='123', group_role='STD')
        self.item = Item.objects.create(nome="Rashguard", tipo="RASHGUARD", valor=120.00, quantidade=3)
        self.novo_pedido_url = reverse('aluno_pedido_novo')

    def test_aluno_pedido_novo_view_unauthenticated(self):
        """Testa se um usuário não autenticado é redirecionado da página de novo pedido."""
        response = self.client.get(self.novo_pedido_url)
        self.assertEqual(response.status_code, 302) # 302 é o código para redirecionamento
        self.assertRedirects(response, f"{reverse('login')}?next={self.novo_pedido_url}")

    def test_aluno_pedido_novo_view_authenticated_student(self):
        """Testa se um aluno autenticado consegue acessar a página de novo pedido."""
        self.client.login(username='aluno', password='123')
        response = self.client.get(self.novo_pedido_url)
        self.assertEqual(response.status_code, 200) # 200 é o código para OK
        self.assertTemplateUsed(response, 'academia/aluno/pedido_form.html')

    def test_aluno_cria_pedido_com_sucesso(self):
        """Testa a criação de um pedido via POST e a baixa no estoque."""
        self.client.login(username='aluno', password='123')
        initial_stock = self.item.quantidade
        
        form_data = {'item': self.item.id, 'quantidade': 1}
        response = self.client.post(self.novo_pedido_url, data=form_data)

        # Verifica se foi redirecionado para a lista de pedidos
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('aluno_pedidos'))

        # Verifica se o pedido foi criado no banco
        self.assertEqual(Pedido.objects.count(), 1)
        pedido = Pedido.objects.first()
        self.assertEqual(pedido.aluno, self.student_user)
        self.assertEqual(pedido.item, self.item)
        self.assertEqual(pedido.quantidade, 1)

        # Verifica se o estoque foi atualizado (reserva)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade, initial_stock - 1)

class ManagementCommandTests(TestCase):
    """
    Testes para os Management Commands.
    """
    def setUp(self):
        self.item = Item.objects.create(nome="Kimono", tipo="KIMONO", valor=400.00, quantidade=10)
        self.student = User.objects.create_user(username='teststudent', password='123', group_role='STD')

    def test_cancel_expired_orders_command(self):
        """Testa o comando que cancela pedidos expirados."""
        # 1. Cria um pedido que deve expirar
        old_date = timezone.now() - timedelta(days=16)
        expired_order = Pedido.objects.create(
            aluno=self.student,
            item=self.item,
            quantidade=2,
            status='PEND'
        )
        # Manually set the date, as auto_now_add is tricky to override in tests
        expired_order.data_solicitacao = old_date
        expired_order.save()

        # 2. Cria um pedido recente que não deve expirar
        recent_order = Pedido.objects.create(
            aluno=self.student,
            item=self.item,
            quantidade=3,
            status='PEND'
        )

        # 3. Deduz o estoque para simular a reserva
        self.item.quantidade -= 5
        self.item.save()
        self.assertEqual(self.item.quantidade, 5)

        # 4. Executa o comando
        out = StringIO()
        call_command('cancel_expired_orders', stdout=out)

        # 5. Verifica os resultados
        expired_order.refresh_from_db()
        self.assertEqual(expired_order.status, 'CANC')
        self.assertEqual(expired_order.cancellation_reason, 'Expirado tempo para atendimento')

        recent_order.refresh_from_db()
        self.assertEqual(recent_order.status, 'PEND')

        # 6. Verifica se o estoque do item expirado foi devolvido
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantidade, 5 + 2) # Estoque restante + quantidade devolvida

        # 7. Verifica a saída do comando
        self.assertIn(f'Pedido #{expired_order.id} para "Kimono" cancelado. 2 unidade(s) devolvida(s) ao estoque.', out.getvalue())
        self.assertIn('Operação concluída. 1 pedido(s) expirado(s) foram cancelados.', out.getvalue())
