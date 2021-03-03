import socket
import os
from _thread import *
import sqlite3


conn = sqlite3.connect('main_db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("SELECT * FROM Persons")
database = cursor.fetchall()

class Klient:
    def __init__(self, firstname, lastname, nrpesel, nrkonta, pin = '0000', saldo = 0):
        self.firstname = firstname
        self.lastname = lastname
        self.nrpesel = nrpesel
        self.nrkonta = nrkonta
        self.saldo = saldo
        self.pin = pin
        self.addToSQL()    ## Uncomment it for auto add clients to database

    def addToSQL(self):
        isReady = True
        values = [self.firstname, self.lastname, self.nrpesel, self.nrkonta, self.pin, self.saldo]
        for i in database:
            if (i[2] == self.nrpesel):
                isReady = False
        if (isReady):
            cursor.execute(
                "INSERT INTO Persons (FirstName, LastName, nrPesel, nrKonta, pin, Saldo) VALUES (?, ?, ?, ?, ?, ?)",
                values)
            conn.commit()
            print('The ' + self.firstname + ' ' + self.lastname + ' has been added to the database')
        else:
            print('The ' + self.firstname + ' ' + self.lastname + ' is already in the database')

    def toArray(self):
        self.arr = []
        self.arr.append(self.firstname)
        self.arr.append(self.lastname)
        self.arr.append(self.nrpesel)
        self.arr.append(self.nrkonta)
        self.arr.append(self.saldo)

# Example for create new client :
#     example = Klient('Marcin', 'Selecki', 90080700000, 123412349, here you can add pin, it must be string and have 4 number, for example: '1234')
# p1 = Klient('Mykyta', 'Burdeniuk', 99112100000, 123456789)
#
# p2 = Klient('Mateusz', 'Kozanowski', 99231341123, 543214321, '1234') Here we create new client and added PIN, is automatically set '0000'


ServerSideSocket = socket.socket()
host = '127.0.0.1'
port = 2004
ThreadCount = 0
try:
    ServerSideSocket.bind((host, port))
except socket.error as e:
    print(str(e))

print('Socket is listening..')
ServerSideSocket.listen(5)

operations = ['1 - Saldo \n', '2 - wplata gotowki \n', '3 - wyplata gotowki \n', '4 - przelew bankowy \n']

def multi_threaded_client(connection):
    connection.sendall(str.encode('-----------------------------Witamy w Marcin Selecki / Mykyta Burdeniuk BANK-----------------------------\n'
                                  'Logowanie do systemy...\n'))
    isLoggin = False
    while True:
        cursor.execute("SELECT * FROM Persons")
        database = cursor.fetchall()

        if (not isLoggin):
            while True:
                isntHave = True
                connection.sendall(str.encode('nrPesel:'))
                login = connection.recv(2048)
                login = int(login.decode('utf-8'))

                for i in database:
                    if (i[2] == login):
                        isntHave = False
                        while True:
                            connection.sendall(str.encode('PIN:'))
                            data = connection.recv(2048)
                            data = data.decode('utf-8')
                            if (data == i[5]):
                                connection.sendall(str.encode('Welcome!\nPress enter to continue...'))
                                isLoggin = True
                                break
                            else:
                                connection.sendall(str.encode('Zle podales PIN. Sproboj ponownie...\n'))
                                continue
                if (isLoggin):
                    break
                if (isntHave):
                    connection.sendall(str.encode('\nNie ma takiego konta. Sproboj ponownie...\n'))
                    continue


        connection.sendall(str.encode('1 - Saldo \n2 - wplata gotowki \n3 - wyplata gotowki \n4 - przelew bakowy \nWybierz operacje: '))
        counter = 0
        data = connection.recv(2048)
        data = data.decode('utf-8')
        if not data:
            break
        if (data =='1'):
            cursor.execute("SELECT * FROM Persons")
            database = cursor.fetchall()

            for i in database:
                if (i[2] == login):
                    print(login)
                    connection.sendall(str.encode('Saldo:' + str('%.2f' % i[4]) + 'zl.\nPress enter to continue...\n'))
        elif (data == '2'):
            cursor.execute("SELECT * FROM Persons")
            database = cursor.fetchall()

            connection.sendall(str.encode('Wpisz kwote wplaty: '))
            kwota = connection.recv(2048)
            kwota = kwota.decode('utf-8')

            for i in database:
                if (i[2] == login):
                    counter=counter+1
                    konto = i[3]
                    Saldo = i[4]


            if (counter == 0):
                connection.sendall(str.encode('Nie znaleziono konta.\nPress enter to continue...\n'))
                continue


            connection.sendall(str.encode('Dokonano wplaty: ' + kwota + 'zl. Saldo: ' + str('%.2f' % (Saldo+int(kwota))) + 'zl.\nPress enter to continue...\n'))

            kwota = int(kwota)
            konto = int(konto)
            purchases = [kwota, konto]

            cursor.execute('UPDATE Persons SET Saldo=Saldo + ? WHERE nrKonta = ?', purchases)
            conn.commit()

            continue

        elif (data == '3'):
            cursor.execute("SELECT * FROM Persons")
            database = cursor.fetchall()

            connection.sendall(str.encode('Wpisz kwote wyplaty: '))
            kwota = connection.recv(2048)
            kwota = kwota.decode('utf-8')

            counter = 0
            for i in database:
                if (i[2] == login):
                    counter=counter+1
                    Saldo = i[4]

            if (counter == 0):
                connection.sendall(str.encode('Nie znaleziono konta.\nPress enter to continue...\n'))
                continue

            for i in database:
                if (i[3] == int(konto)):
                    if (i[4]<int(kwota) or i[4] < 0):
                        connection.sendall(str.encode('Masz niewystarczajaco srodkow na koncie dla tej operacji. Masz:' + str(i[4]) + 'zl na koncie.\nBrakuje do tej operacji: '
                                                      + str(int(kwota) - i[4]) + 'zl\nPress enter to continue...\n'))
                        kwota='0'
                        continue


            connection.sendall(str.encode('Kwota wyplaty: ' + kwota + 'zl. Saldo: ' + str('%.2f' % (Saldo - int(kwota))) + '\nPress enter to continue...\n'))

            kwota = int(kwota)
            konto = int(konto)
            purchases = [kwota, konto]

            cursor.execute('UPDATE Persons SET Saldo=Saldo - ? WHERE nrKonta = ?', purchases)
            conn.commit()
            results = cursor.fetchall()

            for i in results:
                connection.sendall(str.encode(i))

        elif (data == '4'):
            cursor.execute("SELECT * FROM Persons")
            database = cursor.fetchall()

            correct = True

            for i in database:
                if (i[2] == login):
                    nrKonta = i[3]


            connection.sendall(str.encode('Wpisz kwote przelewu: '))
            kwota = connection.recv(2048)
            kwota = kwota.decode('utf-8')

            for i in database:
                if (i[2] == login):
                    if(i[4]<int(kwota)):
                        connection.sendall(str.encode(
                            'Masz niewystarczajaco srodkow na koncie dla tej operacji. Masz:' + str(
                                i[4]) + 'zl na koncie.\nBrakuje do tej operacji: '
                            + str(int(kwota) - i[4]) + 'zl\nPress enter to continue...\n'))
                        correct = False
                        continue

            if(correct):
                connection.sendall(str.encode('Wpisz numer konta docelowego: '))
                konto = connection.recv(2048)
                konto = konto.decode('utf-8')
                counter = 0
                for i in database:
                    if (i[3] == int(konto)):
                        counter = counter + 1
                        purchases = [kwota, nrKonta]
                        cursor.execute('UPDATE Persons SET Saldo=Saldo - ? WHERE nrKonta = ?', purchases)
                        purchases = [kwota, konto]
                        cursor.execute('UPDATE Persons SET Saldo=Saldo + ? WHERE  nrKonta = ?', purchases)
                        conn.commit()
                        results = cursor.fetchall()

                        connection.sendall(str.encode(
                            'Przelew na konto: ' + konto + '. Kwota: ' + kwota + 'zl wykonano!' + '\nPress enter to continue...\n'))

            if (counter == 0):
                connection.sendall(str.encode('Nie znaleziono konta.\nPress enter to continue...\n'))
                continue



    connection.close()

while True:
    Client, address = ServerSideSocket.accept()
    print('Connected to: ' + address[0] + ':' + str(address[1]))
    start_new_thread(multi_threaded_client, (Client, ))
    ThreadCount += 1
    print('Thread Number: ' + str(ThreadCount))


conn.close()


ServerSideSocket.close()