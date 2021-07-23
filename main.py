from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLineEdit, QLabel, QCheckBox, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from dicttoxml import dicttoxml
import xmltodict
import urllib
import sys
import time
import spotipy
import spotipy.util as util

## ver 2 - Jan 13, 2021
## instead of checking playlist every time in internet,
## we checked from an xml file that we created with this application
## this made application faster

username = 'your_username'
scope = 'user-library-read, playlist-read-private'
token = util.prompt_for_user_token(username, scope,
                           client_id='your_client_id',
                           client_secret='your_client-secret',
                           redirect_uri='your_redirect_uri(ex:http://localhost:6169/)')

sp = spotipy.Spotify(auth=token)

numof_playlists = sp.current_user_playlists()['total']
all_playlists = []
# 50 is max returned number of playlists by current_user_playlists() it's default 50 in func
for i in range(0, numof_playlists + 50, 50):
    all_playlists += sp.current_user_playlists(offset=i)['items']


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("mainwindow.ui", self)

        self.txt_uri           = self.findChild(QLineEdit,   "txt_uri")
        self.txt_track_name    = self.findChild(QLineEdit,   "txt_track_name")
        self.txt_track_artist  = self.findChild(QLineEdit,   "txt_track_artist")
        self.btn_search        = self.findChild(QPushButton, "btn_search")
        self.btn_create_xml    = self.findChild(QPushButton, "btn_create_xml")
        self.btn_info          = self.findChild(QPushButton, "btn_info")
        self.lbl_chro          = self.findChild(QLabel,      "lbl_chro")
        self.lbl_track_img     = self.findChild(QLabel,      "lbl_track_img")
        self.chk_show_track    = self.findChild(QCheckBox,   "chk_show_track")

        self.btn_search.clicked.connect(self.btn_search_clicked)
        self.btn_create_xml.clicked.connect(self.create_xml)
        self.btn_info.clicked.connect(self.show_app_info)

        self.show()

    def show_app_info(self):
        info =  """Before start, you have to create a database by using 'UPDATE XML' button.
This button creates an xml file containing your playlists on your spotify.
How long it takes depends on how many songs you have.

After you can enter the URI of the song you will check in the textbox on the left. To get URI;
Spotify --> Song --> More(or Right Click) --> Share --> Copy Spotify URI """
        QMessageBox.information(self, 'ABOUT APP', info)

    # playlists to xml
    def create_xml(self):
        all_tracks = []
        for playlist in all_playlists:
            results = sp.playlist_tracks(playlist['id'])
            all_tracks.append(results)
            while results['next']:
                results = sp.next(results)
                all_tracks.append(results)

        xml = dicttoxml(all_tracks, custom_root='the_root', attr_type=False) # each playlist consists max 100 track

        with open('all_playlists.xml', 'wb') as f:
            f.write(xml)


    def show_track_info(self):
        txt_uri_value = self.txt_uri.text()
        track = sp.track(txt_uri_value)
        track_name    = track['name']
        track_artist  = ""
        for artist in track['artists']:
            track_artist += artist['name']
            track_img_url = track['album']['images'][0]['url']


            ## setting label's image as track's image
            data = urllib.request.urlopen(track_img_url).read()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            pixmap = pixmap.scaled(240, 240)
            self.lbl_track_img.setPixmap(pixmap)
            self.txt_track_name.setText(track_name)
            self.txt_track_artist.setText(track_artist)


    def btn_search_clicked(self):
        self.lbl_track_img.clear()
        self.txt_track_name.clear()
        self.txt_track_artist.clear()
        self.lst_playlists.clear()

        start = time.time()
        txt_uri_value = self.txt_uri.text()

        try:
            with open('all_playlists.xml', 'r') as f:
                playlists_ordict = xmltodict.parse(f.read())
        except Exception as e:
            QMessageBox.critical(self, 'ERROR', str(e))
            sys.exit(app.exec_())

        """
        -the_root          # playlists in one tag
            -item              # playlists              ---> list
                -items             # tracks in one playlist
                    -item              # tracks                 ---> list
                        ...                # track infos
                    /item
                /items
            /item
        /the_root
        """

        playlists_list = playlists_ordict['the_root']['item']
        for playlist in playlists_list:
            tracks = playlist['items']              # list
            for track in tracks['item']:
                if(track['track'] is not None):
                    if(track['track']['uri'] == txt_uri_value):
                        id = playlist['href'].split('/')[-2]    # second to last
                        playlist_name = sp.playlist(playlist_id=id)['name']
                        self.lst_playlists.addItem(playlist_name)

        ## showing track's info
        if(self.chk_show_track.isChecked()):
            self.show_track_info()

        end = time.time()
        self.lbl_chro.setText(str(end - start))

    ## end of class UI

app = QApplication(sys.argv)

UIWindow = UI()
app.exec_()
