from db_config import init_db

def main():
    print("--- Inicializando Proyecto CAVA ---")
    init_db()
    print("--- Proceso finalizado ---")

if __name__ == '__main__':
    main()
