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
        $ git clone https://github.com/lctheodoro/LibraryFree.git
        ```
2. Entre no repositório  
        ```
        $ cd libraryfree
        ```
3. Instale o virtualenv  
        ```
        $ pip install virtualenv
        ```
4. Crie um novo virtualenv  
        ```
        $ virtualenv -p python3 flask
        ```
5. Execute o virtualenv  
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
        ```
        ```
        $ export LIBRARYFREE_DB_URI="postgres:///libraryfree"  
        ```
8. Crie o banco de dados *libraryfree* no seu PostgreSQL local
9. Realizar as *migrations* do banco de dados  
        ```
        $ python3 run.py db init
        ```  
        ```
        $ python3 run.py db migrate
        ```  
        ```
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

A descrição da API encontra-se no [Google Drive](https://docs.google.com/document/d/11MZLz1n1NyYSTxpYS7F2cb73usuK1KQio-7rnuB214w/edit). Siga os padrões deste documento para contribuir com o desenvolvimento do aplicativo.  

## Estudo
Para compreender a forma como essa API funciona, por favor referir-se abaixo.  

1. Se você ainda não conhece Python, estude os seguintes materiais:  
        1.1 [Vídeo aulas - Python para Zumbis](http://pycursos.com/python-para-zumbis/)  
        1.2 [Vídeo aulas - Fundamentos da Programação com Python](https://br.udacity.com/course/programming-foundations-with-python--ud036/)  
        1.3 [Artigo - Guia para Iniciantes](https://ericstk.wordpress.com/2013/01/02/python-guia-para-iniciantes-a-programacao/)  
2. Se você ainda não conhece Flask, estude os seguintes materiais:  
        2.1 [Vídeo aulas - Flask por Julia Rizza](https://drive.google.com/drive/folders/0B2z6DzJRIzgOTHRTTnF5RHpfeDQ?usp=sharing)  
        2.2 [Vídeo aulas - Full-Stack Foundations](https://br.udacity.com/course/full-stack-foundations--ud088/)  
        2.3 [Artigos - Flask Mega-tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)  
3. Se você ainda não conhece APIs RESTFul, estude os seguintes materiais:  
        3.1 [Vídeo aulas - REST API Tutorial](http://www.restapitutorial.com/)  
        3.2 [Artigo - Uma rápida introdução ao REST](https://www.infoq.com/br/articles/rest-introduction)  
4. Se você ainda não sabe trabalhar com APIs REST no Flask, estude os seguintes materiais:  
        4.1 [Vídeo aulas - Designing RESTful APIs](https://br.udacity.com/course/designing-restful-apis--ud388/)  
        4.2 [Artigo - APIs RESTful com Python e Flask](https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask)  
        4.3 [Artigo - APIs RESTful com Flask-RESTful](https://blog.miguelgrinberg.com/post/designing-a-restful-api-using-flask-restful)  
        4.4 [Artigo - Autenticação RESTful com Flask](https://blog.miguelgrinberg.com/post/restful-authentication-with-flask)
