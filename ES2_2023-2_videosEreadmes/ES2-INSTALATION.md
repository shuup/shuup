# Tutorial de instalação do projeto

Agora com as manutenções necessárias, o projeto pode ser implementado com os seguintes requisitos:
- Python (versão 3.6)
- Node.js
- SQLite


Primeiramente, clone o repositório e na pasta do projeto crie um ambiente virtual

```
 virtualenv shuup-venv
 . shuup-venv/bin/activate
```

Agora para instalar a versão de desenvolvimento do projeto, passamos um pip install por todos os requisitos:

```
pip install -r requirements-dev.txt
```

Agora para buildar a workbench de Django utilizada, que trata basicamente de uma versão contida de uma database SqlLite para rodar o projeto:

```
# Migrate database.
python -m shuup_workbench migrate

# Import some basic data.
python -m shuup_workbench shuup_init

# Create superuser so you can login admin panel
python -m shuup_workbench createsuperuser

# Run the Django development server (on port 8000 by default).
python -m shuup_workbench runserver
```

Com o runserver você pode testar a aplicação, mas para realmente utilizá-la, precisamos instalar alguns recursos web extras, como por exemplo, o CSS.

```
python setup.py build_resources
```

Com isso, você possui uma versão funcional rodando do projeto em questão!
