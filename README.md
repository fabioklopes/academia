# Sistema de Controle de Presenças e Faltas - Academia de Jiu-Jitsu

Sistema desenvolvido em Python, Django e SQLite para gerenciamento de uma academia de Jiu-Jitsu.

## Características

### Usuários e Permissões

- **Aluno (STD)**: Acesso ao Painel do Aluno
- **Professor (PRO)**: Acesso completo ao sistema
- **Administrador (ADM)**: Controle total, incluindo designação de professores

### Painel do Aluno

1. **Marcar Presença**: Calendário para selecionar uma ou mais datas e enviar solicitação
2. **Cancelar Solicitação**: Cancelar presenças pendentes
3. **Visualizar Presenças**: Ver status (aprovadas, rejeitadas, pendentes) com motivo de rejeição
4. **Relatórios**: Relatórios mensais ou por período personalizado
5. **Perfil**: Edição de dados pessoais e upload de foto (via arquivo ou câmera)

### Painel do Professor

1. **Gerenciar Turmas**: Criar, editar e desativar turmas
2. **Aprovar/Rejeitar Cadastro**: Aprovar solicitações de alunos em turmas
3. **Desativar Alunos**: Alterar status de aluno para inativo
4. **Aprovar/Rejeitar Presenças**: Filtrar e gerenciar solicitações de presença
5. **Controle de Graduação**: Gerenciar faixas e graus dos alunos
6. **Planos de Aula**: Criar e gerenciar planos de aula
7. **Rankings**: Criar rankings internos (menos faltas, mini-campeonatos)
8. **Controle de Pedidos**: Gerenciar pedidos (Kimonos, Faixas, Hashguards, Exames, etc.)
9. **Relatórios**: Relatórios completos sobre todas as áreas

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Execute as migrações:
```bash
python manage.py migrate
```

3. Crie um superusuário:
```bash
python manage.py createsuperuser
```

4. Execute o servidor:
```bash
python manage.py runserver
```

## Estrutura do Projeto

- `academia/`: Aplicação principal
  - `models.py`: Modelos de dados (User, Turma, Presenca, Graduacao, etc.)
  - `views.py`: Views e lógica de negócio
  - `templates/`: Templates HTML
  - `admin.py`: Configuração do admin do Django

## Banco de Dados

O sistema utiliza SQLite por padrão. O arquivo `database.db` será criado automaticamente após as migrações.

## Observações

- O sistema usa Bootstrap 5 para o frontend
- As fotos dos usuários são armazenadas na pasta `media/photos/`
- O sistema suporta upload de foto via arquivo ou câmera do dispositivo

