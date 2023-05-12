import datetime
from flask import Flask, redirect, render_template, request
import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash
import flask_login

app = Flask(__name__)

################__________________SQL_____________________###############

# TODO sprawdzić standart obsługi sql.connect()

def get_db_connection():
   con = sql.connect('wsb.sqlite')
   con.row_factory = sql.Row
   return con


def sql_query(query_insert):
   con = get_db_connection()
   cur = con.cursor()
   cur.execute(query_insert)
   con.commit()
   con.close()


def sql_insert(query_insert):
   sql_query(query_insert)
   
   
def sql_delete(query_delete):
   sql_query(query_delete)


def sql_update(query_update):
   sql_query(query_update)
   
 
def sql_select(query_select):
   con = get_db_connection()
   cur = con.cursor()
   cur.execute(query_select)
   # row = [r for r in cur.fetchall() if r is not None]
   row = cur.fetchall()
   con.close()
   return row

# zastąpienie "None" na string = ""
def delete_none(row):
   row_dict = dict(row[0])
   for key, value in row_dict.items():
      if value is None:
         row_dict[key] = ""
   return row_dict

################______________Uploading Files_________________###############
# TODO Create code for uplaud file

################__________________LOGIN_____________________###############

#__________________load users from sql_____________________

def load_users():
   query_select = f"SELECT * FROM users"
   rows = sql_select(query_select)
   users = {}
   for row in rows:
      # print(f"ID: {row[0]}\nlogin_email: {row[1]}\nName: {row[2]}\nPassword: {row[3]}")
      user = {row[1]: {'name': row[4],'password': row[2], 'rank': int(row[3])}}
      users.update(user)
   return users

#__________________flask login_____________________

app.secret_key = '*\xf6\x02\x004\xed\x93\x0cq/\x97\x9b\x0e\x06&\xc2\x91\xe8\xdb\x84\x10\xdfl\xc8'  # Change this!
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
users = load_users()


class User(flask_login.UserMixin):
    pass


@login_manager.request_loader
def request_loader(request):
   login_email = request.form.get('login_email')   # Pobierz z formularza na stronie logowanie.
   if login_email not in users:
      return
   user = User()
   user.id = login_email
   user.rank = users[login_email]['rank']
   user.name = users[login_email]['name']
   return user


@login_manager.user_loader
def user_loader(login_email):
   if login_email not in users:
      return
   user = User()
   user.id = login_email
   user.rank = users[login_email]['rank']
   user.name = users[login_email]['name']
   return user


@app.route('/login', methods=['GET', 'POST'])
def login():
   error = ""
   
   # FIXME dokończyć formularz wiadomośći dla UR!
   action = request.args.get('action', default = '', type = str)
   print(action)
   if action =='send':
      rows = {}
      rows.clear()
      rows['notifier'] = request.args.get('notifier', default = '', type = str)
      rows['message'] = request.args.get('message', default = '', type = str)
      rows['type_message'] = request.args.get('type_message', default = '', type = str)
      rows['date_addet'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      print("GET:", rows['notifier'], rows['message'], rows['type_message'], rows['date_addet'])
      
      if all(rows.values()): 
         query_select = f"INSERT INTO message (notifier, message, type_message, date_added) \
                           VALUES('{rows['notifier']}', '{rows['message']}', '{rows['type_message']}', '{rows['date_addet']}')"      
         sql_insert(query_select)
         info = 'Wiadomość została wysłana.'
      else:
         info = 'Nie wypełniłeś wszystkich pól.'
      return render_template('login.html', error=info)
      #----- wiadomość dla UR END
      
   if request.method == 'POST':
      login_email = request.form['login_email']
      if login_email in users and check_password_hash(users[login_email]['password'], request.form['password']):
         user = User()
         user.id = login_email
         flask_login.login_user(user)
         return redirect('/')  #return redirect(url_for('protected'))
      error = 'Złe hasło!'
   return render_template('login.html', error=error)


@app.route('/protected') # Tylko dla testów!
@flask_login.login_required
def protected():
   return 'Nane: ' + flask_login.current_user.name + ' | Logged in as: ' + flask_login.current_user.id +' | Rank is: ' + str(flask_login.current_user.rank)
 
 
@app.route('/logout')
def logout():
   flask_login.logout_user()
   return redirect('/')


@login_manager.unauthorized_handler
def unauthorized_handler():
   return redirect('/login')
   # return render_template('login.html'), 401

################__________________HOMEPAGE_____________________###############

@app.route('/')
@flask_login.login_required
def base():
   query_select = f"SELECT * FROM message"
   rows = sql_select(query_select)
   return render_template('index.html', rows=rows)

################__________________FAILURE_____________________###############

@app.route('/management-failure', methods = ['POST', 'GET'])
@flask_login.login_required
def failures():
   rows_per_page = 30   # Ilość zgłoszeń na stronie
   #Dotyczny edycji zgłoszenia
   id_db = request.args.get('id', default = '', type = int)
   action = request.args.get('action', default = '', type = str)
   #Parametry głownej strony z listą zgłoszeń.
   nr_page = request.args.get('page', default = 1, type = int)
   search = request.args.get('search', default = '', type = str)
   #Parametry głownej strony z listą zgłoszeń.
   if request.method == 'POST':
      if 'action' in request.form:
         rows = {}
         rows.clear()
         rows['linia'] = request.form['linia']
         rows['maszyna'] = request.form['maszyna']
         rows['rodzaj'] = request.form['rodzaj']
         rows['typ'] = request.form['typ']
         
         # TODO Complete file handling
         # rows['formFileMultiple'] = request.form['formFileMultiple']
         # f = rows['formFileMultiple']
         # f.save(f.filename)  
         # return render_template("Acknowledgement.html", name = f.filename)  
  
         # Możliwość przypisanie przez lidera osoby odpowiedziialnej do zgłoszenia
         rows['zgloszenie'] = request.form['zgloszenie']
         if "responsible" in request.form and request.form['responsible']:
            rows['mechanik'] = request.form['responsible']
         else:
            rows['mechanik'] = flask_login.current_user.name
            
         if all(rows.values()): 
            currentDateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # # Definiowanie zapytania z użyciem prepared statements
            # query_select = "INSERT INTO awarie (requestor, mechanik, linia, maszyna, rodzaj, typ, zgloszenie, czas_start) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            # # Wykonanie zapytania z użyciem wartości parametrów
            # params = (rows['requestor'], rows['mechanik'], rows['linia'], rows['maszyna'], rows['rodzaj'], rows['typ'], rows['zgloszenie'], currentDateTime)
            query_select = f"INSERT INTO awarie (requestor, mechanik, linia, maszyna, rodzaj, typ, zgloszenie, czas_start) VALUES('{flask_login.current_user.name}', '{rows['mechanik']}', '{rows['linia']}', '{rows['maszyna']}', '{rows['rodzaj']}', '{rows['typ']}', '{rows['zgloszenie']}', '{currentDateTime}')"
            sql_insert(query_select)
            return redirect('/management-failure')

   #Obsługa przycisku "Zapis" w edycji zgłoszenia, jeżeli otrzyma GET
   # TODO Usunąć nie potrzebne request, nie używane do zapytania SQL
   if action == "save":
      rows = {}
      rows.clear()
      rows['update_id'] = request.args.get('update_id', default = '', type = str)
      rows['requestor'] = request.args.get('requestor', default = '', type = str)
      rows['czas_start'] = request.args.get('czas_start', default = '', type = str)
      rows['czas_stop'] = request.args.get('czas_stop', default = '', type = str)
      rows['czas_trwania'] = request.args.get('czas_trwania', default = '', type = str)
      rows['status'] = request.args.get('status', default = '', type = str)
      rows['przyczyna'] = request.args.get('przyczyna', default = '', type = str)
      rows['opis'] = request.args.get('opis', default = '', type = str)
      rows['linia'] = request.args.get('linia', default = '', type = str)
      rows['maszyna'] = request.args.get('maszyna', default = '', type = str)
      rows['rodzaj'] = request.args.get('rodzaj', default = '', type = str)
      rows['typ'] = request.args.get('typ', default = '', type = str)
      rows['zgloszenie'] = request.args.get('zgloszenie', default = '', type = str)
      rows['part_new'] = request.args.get('part_new', default = '', type = str)  # TODO JESZCZE nie dodano do bazy danych
      rows['part_reg'] = request.args.get('part_reg', default = '', type = str)  # TODO JESZCZE nie dodano do bazy danych

      print("part_new:", rows['part_new'], "part_reg:", rows['part_reg'])
      currentDateTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      # query_update = "UPDATE awarie SET requestor=?, czas_start=?, czas_stop=?, czas_trwania=?, linia=?, maszyna=?, typ=?, rodzaj=?, status=?, zgloszenie=?, przyczyna=?, opis=? WHERE id=?"
      # params = (rows['requestor'], rows['czas_start'], currentDateTime, rows['czas_trwania'], rows['linia'], rows['maszyna'], rows['typ'], rows['rodzaj'], rows['status'], rows['zgloszenie'], rows['przyczyna'], rows['opis'], rows['update_id'])
      query_update = f"UPDATE awarie SET requestor='{rows['requestor']}', czas_start='{rows['czas_start']}', czas_stop='{currentDateTime}', czas_trwania='{rows['czas_trwania']}', linia='{rows['linia']}', maszyna='{rows['maszyna']}', typ='{rows['typ']}', rodzaj='{rows['rodzaj']}', status='{rows['status']}', zgloszenie='{rows['zgloszenie']}', przyczyna='{rows['przyczyna']}', opis='{rows['opis']}' WHERE id='{rows['update_id']}'"
      sql_update(query_update)
      return redirect('/management-failure')

      
   #Obsługa przycisku "Delate" w edycji zgłoszenia
   elif id_db and action == 'delete':  #HACK and flask_login.current_user.rank >= 3
      query_delete = f"DELETE FROM awarie WHERE id='{id_db}'"
      sql_delete(query_delete)
      return render_template('delete.html')
   
   #Nie przejdzie do edycji zgłoszenia, jeżeli nie ma ID w URL zgłoszenia.
   elif id_db and not action:
      #Pobieranie z bazy danych konkretnego zgłoszenia"
      query_select = f"SELECT * FROM awarie WHERE id LIKE '{id_db}'"
      row = sql_select(query_select)
      row_dict = delete_none(row)
      
      #Pobieranie z bazy danych wpisów częsci dla opcji "Pobierz część"
      query_select = "SELECT * FROM warehouse ORDER BY nazwa DESC"
      rows = sql_select(query_select)
      return render_template('failures.html', row = row_dict, rows=rows)
      
   # Obsługa przycisku "Szukaj", w główny oknie, pobiera z URL
   elif search:
      color_info_list = {1: 'class=table-danger', 2: 'class=table-warning', 3: 'class=table-success', 4: 'class=table-secondary', 5: ''}
      query_select = f"SELECT * FROM awarie WHERE linia LIKE '%{search}%' OR maszyna LIKE '%{search}%' OR requestor LIKE '%{search}%' OR zgloszenie LIKE '%{search}%' OR mechanik LIKE '%{search}%' OR czas_start LIKE '%{search}%' ORDER BY czas_start DESC"
      rows = sql_select(query_select)
      return render_template("management-failure.html", rows = rows, color_info = color_info_list)
   
   #Jeżli nie będą spełniać wszystkie powyższe warunki, wczytaj liste zgłoszeń.

   max_iteam = sql_select(f"SELECT COUNT(id)FROM awarie")
   max_iteam = int(max_iteam[0][0])
   max_page = int(max_iteam/rows_per_page)
   offset_row = str(rows_per_page*(nr_page-1))
   
   #lista color_info_list do oznaczenia Awarii, Usterki,Usprawnie, BHP
   color_info_list = {1: 'class=table-danger', 2: 'class=table-warning', 3: 'class=table-success', 4: 'class=table-secondary', 5: ''}
   
   # Pobiera wpisy tylko na wyświetloną strone "LIMIT"!
   query_select = f"SELECT * FROM awarie ORDER BY czas_start DESC LIMIT {rows_per_page} OFFSET {offset_row} "
   rows = sql_select(query_select)
   
   # Pobiera wszystkie wpisy dla funkcji "Oczekujące zgłoszenia"
   query_select = f"SELECT * FROM awarie ORDER BY czas_start DESC"
   rows_all = sql_select(query_select)
   
   # Pobiera wszystkie nazwy mechanikó w celu możliwości przypisania przez lidera zgłoszenia.
   query_select = f"SELECT login FROM users"
   row_mechanic = sql_select(query_select)
   
   # Pobiera wszystkie wpisy lini
   query_select = f"SELECT * FROM Productionline"
   Productionline = sql_select(query_select)
   
   query_select = f"SELECT * FROM Machine"
   Machine = sql_select(query_select)
   
   # Przygodowanie składni do użycia zmiennej w JavaScript: var opcjeMachine = {{machine|safe}}
   machine_as_list = []
   machine_as_dict = {}
   for r in Machine:
      machine_as_list.clear()
      if r["LineID"] in machine_as_dict.keys():
         for temp in machine_as_dict[r["LineID"]]:
            machine_as_list.append(temp)
         machine_as_list.append(r["MachineName"])
      else:
         machine_as_list.append(r["MachineName"])
         machine_as_dict[r["LineID"]] = machine_as_list
      machine_as_dict[r["LineID"]] = machine_as_list.copy()
   
   return render_template("management-failure.html", machine=machine_as_dict, Productionline=Productionline, rows_all=rows_all,  rows=rows, color_info=color_info_list, nr_page=nr_page, max_page=max_page, row_mechanic=row_mechanic)

###############__________________WAREHOUSE_____________________###############

@app.route('/warehouse-inventory')
@flask_login.login_required
def warehouse_inventory():
   # Pobiera wszystkie wpisy dla funkcji "Braki bagazynowe"
   query_select = f"SELECT * FROM warehouse ORDER BY id"  # lokalizacja
   rows = sql_select(query_select)
   return render_template('warehouse-inventory.html', rows = rows)


@app.route('/management-warehouse', methods = ['POST', 'GET'])
@flask_login.login_required
def warehouse_page():
   rows_per_page = 30   # Ilość zgłoszeń na stronie
   search_id = request.args.get('search_id', default = None, type = int)
   search = request.args.get('search', default = '', type = str)
   nr_page = request.args.get('page', default = 1, type = int)
   id_db = request.args.get('id', default = "", type = int)
   
   #lista color_info_list do oznaczenia ilośći częsci na stanie.
   color_info_list = {1: 'class=table-danger', 2: 'class=table-warning', 3: 'class=table-success', 4: 'class=table-secondary', 5: ''}
   
   # Jeśli wykryto klucz "search_id" w URL, filtruj liste części.
   if search_id:
      query_select = f"SELECT * FROM warehouse WHERE id LIKE '{search_id}'"
      rows = sql_select(query_select)
      return render_template("management-warehouse.html", rows = rows, color_info = color_info_list)
    # Obsługa przycisku "Szukaj", w główny oknie, pobiera z URL. Jeśli wykryto klucz "search" w URL,filtruj liste części.

   elif search:
      query_select = f"SELECT * FROM warehouse WHERE nazwa LIKE '%{search}%' OR typ LIKE '%{search}%' OR maszyna LIKE '%{search}%' ORDER BY nazwa DESC"
      rows = sql_select(query_select)
      return render_template("management-warehouse.html", rows = rows, color_info = color_info_list)
   
   # HACK Dostęp tylko dla osób z poziomem 3 i większym.
   # if not flask_login.current_user.rank >= 3:
   #    return render_template('401.html')
   
   # Edytcja i dodawanie wpisuów z częsciami.
   if request.method == 'POST':
      row = {}
      row.clear()
      row['nazwa'] = request.form['nazwa']
      row['typ'] = request.form['typ']
      row['stan_min'] = request.form['stan_min']
      row['ilosc_zam'] = request.form['ilosc_zam']
      row['nowe'] = request.form['nowe']
      row['do_reg'] = request.form['do_reg']
      row['regen'] = request.form['regen']
      row['zlom'] = request.form['zlom']
      if request.form == ['rp']:
         row['rp'] = request.form['rp']
      else:
         row['rp'] = 0
      row['maszyna'] = request.form['maszyna']
      row['lokalizacja'] = request.form['lokalizacja']
      if request.form == ['krytyczne']:
         row['krytyczne'] = request.form['krytyczne']
      else:
         row['krytyczne']  = 0
      row['cena'] = request.form['cena']
      row['opis'] = request.form['opis'] # brak w bazie danych! Nie dodano do INSERT
      row['shop'] = request.form['shop'] # brak w bazie danych! Nie dodano do INSERT
      
      # Zapisanie zmian w trakcie edycji.
      if request.form['action'] == 'save':
         row['update_id'] = request.form['update_id']
         query_update = f"UPDATE warehouse SET nazwa='{row['nazwa']}', typ='{row['typ']}', stan_min='{row['stan_min']}', ilosc_zam='{row['ilosc_zam']}', nowe='{row['nowe']}', do_reg='{row['do_reg']}', regen='{row['regen']}', zlom='{row['zlom']}', rp='{row['rp']}', maszyna='{row['maszyna']}', lokalizacja='{row['lokalizacja']}', krytyczne='{row['krytyczne']}', cena='{row['cena']}' WHERE id='{row['update_id']}'"
         sql_update(query_update)
         return redirect('/management-warehouse')
      
      # Dodanie część do bazy danych.
      if request.form['action'] == 'add-part':
         query_select = f"INSERT INTO warehouse (nazwa, typ, stan_min, ilosc_zam, nowe, do_reg, regen, zlom, rp, maszyna, lokalizacja, krytyczne, cena) VALUES('{row['nazwa']}', '{row['typ']}', '{row['stan_min']}', '{row['ilosc_zam']}', '{row['nowe']}', '{row['do_reg']}', '{row['regen']}', '{row['zlom']}', '{row['rp']}', '{row['maszyna']}', '{row['lokalizacja']}', '{row['krytyczne']}', '{row['cena']}')"
         sql_insert(query_select)
         return redirect('/management-warehouse')
      
      # Usunięcie część do bazy danych.
      if request.form['action'] == 'delete':
         row['update_id'] = request.form['update_id']
         query_delete = f"DELETE FROM warehouse WHERE id='{row['update_id']}'"
         sql_delete(query_delete)
         return redirect('/management-warehouse')
      
   # Nie przejdzie do edycji zgłoszenia, jeżeli ma ID w kluczu URL, generuje z "Braki magazynowe".
   elif id_db:
      # Pobiera wpis dla dla furmulaza w part.html
      query_select = f"SELECT * FROM warehouse WHERE id LIKE '{id_db}'"
      row = sql_select(query_select)
      row_dict = delete_none(row)
      # Pobiera wszystkie wpisy dla funkcji "Braki bagazynowe"
      query_select = f"SELECT * FROM warehouse ORDER BY nazwa DESC"
      rows_all = sql_select(query_select)
      return render_template('part.html', row = row_dict, rows_all = rows_all)
   
   # Wyświetlnienie częsci na liscie, regulacja ilośći wpisów na stronie w zmiennej: rows_per_page =.
   max_iteam = sql_select(f"SELECT COUNT(id)FROM warehouse")
   max_iteam = int(max_iteam[0][0])
   max_page = int(max_iteam/rows_per_page)
   offset_row = str(rows_per_page*(nr_page-1))
   
   # Pobiera wpisy tylko na wyświetloną strone "LIMIT"!
   query_select = f"SELECT * FROM warehouse ORDER BY nazwa DESC LIMIT {rows_per_page} OFFSET {offset_row} "
   rows = sql_select(query_select)
   
   # Pobiera wszystkie wpisy dla funkcji "Braki bagazynowe"
   query_select = f"SELECT * FROM warehouse ORDER BY nazwa DESC"
   rows_all = sql_select(query_select)
   
   return render_template('management-warehouse.html',rows_all=rows_all, rows = rows, color_info = color_info_list, nr_page = nr_page, max_page = max_page)


###############__________________SETTING_____________________###############
# TODO dodać szyfrowanie haseł 

@app.route('/settings', methods = ['POST', 'GET'])
@flask_login.login_required
def settings():
   global users
   info = ''
   if request.method == 'POST':
      if check_password_hash(users[flask_login.current_user.id]['password'], request.form['oldPass']):
         if request.form['newPass1'] == request.form['newPass2']:
            info = 'Zmieniono hasło'
            query_update = f"UPDATE users SET password='{generate_password_hash(request.form['newPass1'])}' WHERE login='{flask_login.current_user.id}'"
            sql_update(query_update)
            users = load_users()
            return render_template('settings.html', info=info)
         else:
            info = 'Hasła nie są jednakowe!'
            return render_template('settings.html', info=info)
      else:
         info = 'Złe hasło!'
         return render_template('settings.html', info=info)
   return render_template('settings.html')

###############__________________OTHER_____________________###############

###############__________________MAIN_____________________###############

if __name__ == '__main__':
   app.run(host='0.0.0.0', debug = True)   # host='0.0.0.0', debug = True