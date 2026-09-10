import mysql.connector as mysq
def db():
    con=mysq.connect(host="localhost",user="root",password="6618",database="warehouse_twin")
    cur=con.cursor()
    print("successfully connected")
