# LibraryFree
Aplicação web e mobile voltada para controle, doação e empréstimo de livros que permite:
* Cadastrar todos os livros que o usuário possui ou que ele deseja adquirir
* Aos usuários Incluir organizações que permitirão o movimento de livros
* Solicitar os livros via sistema e aprovação/negação pelo dono
* Selecionar o processo de entrega (pessoal, Correios, Malote, etc) pelos usuários
* Pontuar de acordo com os empréstimos realizados de forma a ser qualificado publicamente.
* Disponibilizar um Chat para contato
* Gerenciar os empréstimos e devoluções notificando prazos e gerando multas quando houver atrasos
* Solicitar feedbacks após o empréstimo e/ou devolução


## Instalação
Para instalar e executar, siga os seguintes passos:  

1. Clone o repositório

    ```
    $ git clone git@bitbucket.org:juliarizza/libraryfree.git
    ```
    
2. Entre no repositório

    ```
    $ cd libraryfree
    ```
    
3. Instale o `virtualenv`

    ```
    $ pip install virtualenv
    ```
    
4. Crie um novo `virtualenv`

    ```
    $ virtualenv -p python3 flask
    ```
    
5. Execute o `virtualenv`
 
    ```
    $ . flask/bin/activate
    ```
    
6. Instale as dependências
    
    ```
    $ flask/bin/pip3 install -r requirements.txt
    ```

7. Aplique as variáveis de ambiente

    ```
    $ export APP_SETTINGS=config.DevelopmentConfig
    $ export LIBRARYFREE_DB_URI="postgresql:///libraryfree"
    ```

8. Crie o banco de dados *libraryfree* no seu PostgreSQL local
9. Realizar as *migrations* do banco de dados

    ```
    $ python3 run.py db init
    $ python3 run.py db migrate
    $ python3 run.py db upgrade
    ```
    
10. Execute o programa

    ```
    $ python3 run.py runserver
    ```
    
11. Para parar a execução, basta pressionar CTRL+C
12. Para sair do `virtualenv`

    ```
    $ deactivate
    ```

## Ajuda
Para compreender a forma como essa API funciona, por favor referir-se aos seguintes tutoriais:
* [APIs RESTful com Python e Flask](https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask)
* [APIs RESTful com Flask-RESTful](https://blog.miguelgrinberg.com/post/designing-a-restful-api-using-flask-restful)
* [Autenticação RESTful com Flask](https://blog.miguelgrinberg.com/post/restful-authentication-with-flask)

