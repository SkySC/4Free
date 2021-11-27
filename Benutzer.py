import requests


class AmazonBenutzer:
    uid = None
    name = None
    email = None
    plz = None

    def __init__(self, access_token):
        url = 'https://api.amazon.com/user/profile?access_token={}'.format(access_token)
        benutzer_daten = requests.get(url).json()
        print(f'{benutzer_daten=}')
        # Instanzvariablen setzen
        AmazonBenutzer.uid = benutzer_daten['user_id']
        AmazonBenutzer.name = benutzer_daten['name']
        AmazonBenutzer.email = benutzer_daten['email']
        AmazonBenutzer.plz = benutzer_daten['postal_code']

    @staticmethod
    def pruefe_benutzer_eintrag_existiert() -> bool:
        pass

    @staticmethod
    def get_benutzer_namen() -> str:
        return AmazonBenutzer.name

    @staticmethod
    def get_benutzer_email() -> str:
        return AmazonBenutzer.email

    @staticmethod
    def get_benutzer_uid() -> str:
        return AmazonBenutzer.uid

    @staticmethod
    def get_benutzer_land() -> str:
        pass

    @staticmethod
    def get_benutzer_plz() -> int:
        return AmazonBenutzer.plz

    @staticmethod
    def get_benutzer_phone() -> int:
        pass
