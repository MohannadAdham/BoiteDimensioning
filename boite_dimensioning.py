# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BoiteDimensioning
                                 A QGIS plugin
 This plugin calculates automaticaly the dimensions of the boites in a FTTH project
                              -------------------
        begin                : 2018-07-02
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Mohannad ADHAM / Axians
        email                : mohannad.adm@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import PyQt4
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import psycopg2
import psycopg2.extras
import xml.etree.ElementTree as ET
import xlrd
import xlwt
import os.path
import os
import subprocess
import osgeo.ogr  
import processing



from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import QgsMessageBar

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from boite_dimensioning_dialog import BoiteDimensioningDialog
import os.path



class BoiteDimensioning:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'BoiteDimensioning_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)



        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Boite Dimensioning')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'BoiteDimensioning')
        self.toolbar.setObjectName(u'BoiteDimensioning')

        # Create the dialog (after translation) and keep reference
        self.dlg = BoiteDimensioningDialog()

        # Define the levels of a message bar
        self.info = QgsMessageBar.INFO 
        self.critical = QgsMessageBar.CRITICAL
        self.warning = QgsMessageBar.WARNING
        self.success = QgsMessageBar.SUCCESS


#"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""" lsitner autojmatic dimensioning """"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
        
        #creation du bouton "connexion BD"
        Button_connexion_BD= self.dlg.findChild(QPushButton,"pushButton_connexion")
        QObject.connect(Button_connexion_BD, SIGNAL("clicked()"),self.connectToDb)
        #mot de passe en etoile
        self.dlg.lineEdit_Password.setEchoMode(QLineEdit.Password)

        # Connect the button "pushButton_verifier_topologie"
        Button_verification = self.dlg.findChild(QPushButton, "pushButton_verification")
        QObject.connect(Button_verification, SIGNAL("clicked()"), self.verify)

        # Connect the button "pushButton_orientation"
        Button_orientation = self.dlg.findChild(QPushButton, "pushButton_orientation")
        QObject.connect(Button_orientation, SIGNAL("clicked()"), self.calcul_orientation_cable)

        # Connect the button "pushButton_orientation"
        Button_verifier_orientation = self.dlg.findChild(QPushButton, "pushButton_verifier_orientation")  
        QObject.connect(Button_verifier_orientation, SIGNAL("clicked()"), self.verify_orientation_cable)

        # Connect the button "pushButton_fibres_utiles"
        Button_fibres_utiles = self.dlg.findChild(QPushButton, "pushButton_fibres_utiles")
        QObject.connect(Button_fibres_utiles, SIGNAL("clicked()"), self.calcul_fibres_utiles)

        # Connect the button "pushButton_"
        Button_dimensios = self.dlg.findChild(QPushButton, "pushButton_dimensions")
        QObject.connect(Button_dimensios, SIGNAL("clicked()"), self.calcul_boite_dimensions)

        # Connect the butoon "pushButton_mettre_a_jour_chemin"
        Button_verify_capacity = self.dlg.findChild(QPushButton, "pushButton_verify_capacity")
        QObject.connect(Button_verify_capacity, SIGNAL("clicked()"), self.verify_capacite_chambre)

        # Connect the button "pushButton_mettre_a_jour_ebp"
        Button_mettre_a_jour_ebp = self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_ebp")
        QObject.connect(Button_mettre_a_jour_ebp, SIGNAL("clicked()"), self.update_p_ebp)




    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('BoiteDimensioning', message)



    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):


        # Create the dialog (after translation) and keep reference
        # self.dlg = BoiteDimensioningDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/BoiteDimensioning/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Performs boite dimensioning'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Boite Dimensioning'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.GetParamBD(self.dlg.lineEdit_BD, self.dlg.lineEdit_Password, self.dlg.lineEdit_User, self.dlg.lineEdit_Host, self.dlg.Schema_grace)
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass


    def fenetreMessage(self,typeMessage,titre,message):
        """ Display a message box to the user
            titre : the title of the message
            message : the body of the message

        """

        try:
            msg = QMessageBox()
            # msg.setIcon(typeMessage)
            msg.setWindowTitle(titre)
            msg.setText(str(message))
            msg.setWindowFlags(PyQt4.QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage",str(e))


    def sendMessageBar(self, msgType, title, message, timeDur=4):
        """ Display a message to the user in the message bar at the top of the map canvas """

        self.iface.messageBar().pushMessage(title, message, level=msgType, duration=timeDur)        



    def GetParamBD(self, dbname, password, user, serveur, sche):
        ''' Looks for the information to connect to the DB within the QGIS project '''

        try:
            path_absolute = QgsProject.instance().fileName()
            
            if path_absolute != "":
                
                
                tree = ET.parse(path_absolute)
                sche.setText("gracethd")
                root = tree.getroot()

                listeModify = []
                
                for source in root.iter('datasource'):
                    
                    if "dbname" in source.text : 
                        modify = str(source.text)
                        listeModify = modify.split("sslmode")
                        if len(listeModify) > 1:
                            
                            break

                if len(listeModify) > 1 :
                    
                    infosConnexion = listeModify[0].replace("'","")
                    infosConnexion = infosConnexion.split(" ")
                    for info in infosConnexion:
                        inf = info.split("=")
                        if inf[0] == "dbname":
                            dbname.setText(inf[1])
                        if inf[0] == "password":
                            password.setText(inf[1])
                        if inf[0] == "user":
                            user.setText(inf[1])
                        if inf[0] == "host":
                            serveur.setText(inf[1])
                    schemainfo = listeModify[1].replace("'","")
                    schemainfo = schemainfo.split(" ")
                    for sch in schemainfo:
                        sh = sch.split("=")
                        if sh[0] == "table":
                            schema = sh[1].split(".")
                            # sche.setText(schema[0].replace('"',''))
                            sche.setText("gracethd")
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_GetParamBD", str(e))


    def remplir_menu_deroulant_reference(self, combobox, rq_sql, DefValChamp):
        ''' Fill a combobox with a list of table names '''
        listVal = []
        combobox.clear()
        result = self.executerRequette(rq_sql, True)
        for elm in result:
            listVal.append(elm[0])
        combobox.addItems(listVal)
        try:
            combobox.setCurrentIndex(combobox.findText(DefValChamp))
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_remplir_menu_deroulant_reference",str(e))




    def executerRequette(self, Requette, boool):
        ''' Sends a query to execute it within the database and receives the results '''

        global conn
        try:
            cursor = conn.cursor()
            cursor.execute(Requette)
            conn.commit()
            if boool:
                result = cursor.fetchall()
                cursor.close()
                try :
                    if len(result)>0:
                        return result
                except:
                    return None
            else:
                cursor.close()
            
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_executerRequette",str(e))
            cursor.close()




    def connectToDb(self):
        ''' Connects to the DB, enables the comboboxes and the buttons, and fill the comboboxes with the names of the tables '''

        global conn
        Host = self.dlg.lineEdit_Host.text()
        DBname = self.dlg.lineEdit_BD.text()
        User = self.dlg.lineEdit_User.text()
        Password = self.dlg.lineEdit_Password.text()
        Schema = self.dlg.Schema_grace.text()
        Schema_prod = self.dlg.Schema_prod.text()

        
        conn_string = "host='"+Host+"' dbname='"+DBname+"' user='"+User+"' password='"+Password+"'"

        try:
            conn = psycopg2.connect(conn_string)
            #recuperer tout les schemas
            shema_list=[]
            cursor = conn.cursor()
            sql =  "select schema_name from information_schema.schemata "
            cursor.execute(sql)
            result=cursor.fetchall()
            for elm in result:
                shema_list.append(elm[0].encode("utf8"))
            #passer au deuxieme onglet si la connexion est etablit et si le schema existe
            if Schema in shema_list:
                # Do Something
                # Enable the Comboboxes and Buttons

                self.dlg.findChild(QComboBox,"comboBox_suf").setEnabled(True)
                self.dlg.findChild(QComboBox,"comboBox_cable").setEnabled(True)
                self.dlg.findChild(QComboBox,"comboBox_noeud").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_ebp").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_ptech").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_zs_refpm").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_verification").setEnabled(True)
                # self.dlg.findChild(QPushButton, "pushButton_orientation").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_verifier_orientation").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_fibres_utiles").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_dimensions").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_verify_capacity").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_ebp").setEnabled(True)

                # self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_chemin")
                # self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_cable").setEnabled(True)
                # Disable connection button
                self.dlg.findChild(QPushButton, "pushButton_connexion").setEnabled(False)

                # Search for the names of the required tables in each schema
                # 1 - in gracethd
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_suf, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_grace.text()+"' ;"), 't_suf')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_noeud, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_grace.text()+"' ;"), 't_noeud')
                
                # 2 - in prod
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_cable, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_cable')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_ebp, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_ebp')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_ptech, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_ptech') 
                # self.fenetreMessage(QMessageBox.Warning,"Query for zs_refpm", "SELECT zs_refpm FROM " + self.dlg.Schema_grace.text() + ".t_zsro;")
                # result = self.executerRequette("SELECT zs_refpm FROM " + self.dlg.Schema_grace.text() + ".t_zsro;", True)
                # for elm in result:
                #     print elm[0]
                #     self.fenetreMessage(QMessageBox.Warning,"result of query", elm[0])

                # 3 - ZSRO (zs_refpm)
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_zs_refpm, ("SELECT zs_refpm as refpm FROM " + self.dlg.Schema_prod.text() + ".p_zsro ;"), 'PMT_26325_FO01')

                # print "SELECT zs_refpm FROM " + self.dlg.Schema_grace.text() + ".t_zsro;"


                print "Schema found"
                self.sendMessageBar(self.success, "Success", "Connected successfuly to the database", 2)
                # self.dlg2.findChild(QPushButton,"pushButton_controle_avt_migration").setEnabled(True)
            else:

                print "Schema not found"
        except Exception as e:
                pass



    def verify(self):
        """ Performs a set of verifications necessary for the dimensioning of the boites.
        The verifications are the following:
            A. verifications for t_noeud
                1. Doublon géométrie noeud
                2. BAL hors d'une ZPBO
                3. BAL non raccordée à un câble de raccordement
                4. Pavillon (bal entre 1 et 3) dont le nombre de suf est différent du nombre de raccordements
                5. Immeuble (BAL >= 4) dont le nombre de câbles = 0 ou > 1
                6. BAL hors ZSRO

            B. verifications for p_sitetech
                1. Site technique non raccordé à un cable
                2. Doublon géométrie site technique

            C. verifications for p_ebp
                1. Boite non associée à un point technique
                2. Boite sans câble raccordé (boite apparaissant dans t_ebp mais pas dans t_cable cb_bp1,cb_bp2)
                3. PBO sans ZPBO
                4. PBO avec cable de capacité superieure ou égale à 288 FO
                5. Doublon géométrie boite
                6. BPE dans zpbo

            D. verifications for zpbo
                1. ZPBO sans boitier PBO
                2. Doublon de géométrie ZPBO
                3. ZPBO contenant plus d une BAL dont un immeuble
                4. ZPBO contenant une BPE
                5. ZPBO qui a plus d'une boite

            E. verifications for p_cable
                1. Câble avec une capacité invalide
                2. Câble avec capa_fo supérieure ou égale à 288 raccordé sur PBO
                3. Câble sans site technique ou boite en extrémité (vérification géométrique)
                4. Doublons géométrie câble (sans les câbles de racco)
                5. Raccordement sur BPE (vérification attributaire)
                6. Géométrie non valide du câble
                7. Raccordement qui ne part pas d'une boîte ou qui n'arrive pas sur un noeud
                8. Raccordement sur BPE (vérification géométrique)
                9. Raccordement connecté à une mauvaise boîte
                10. Raccordement dont le type logique n'est pas raccordement

        """

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        query_verify = """
        -- verifications for t_noeud

        DROP TABLE IF EXISTS temp.controle_noeud_""" +  zs_refpm.split("_")[2] + """;
        CREATE TABLE temp.controle_noeud_""" +  zs_refpm.split("_")[2] + """ AS
        SELECT row_number() over () id, *
        FROM (
        SELECT 'Topologie' ::varchar As type,'Doublon géométrie noeud' ::varchar As intitule, nd_code, nd_comment, geom 
        FROM gracethd.t_noeud WHERE nd_code IN(SELECT DISTINCT I1.nd_code FROM gracethd.t_noeud I1 
        WHERE EXISTS (SELECT * FROM gracethd.t_noeud I2 WHERE I1.nd_code <> I2.nd_code AND St_Dwithin(I1.geom,I2.geom,0.0001)))

        UNION SELECT 'Structure BDD' ::varchar As type,'BAL hors d''une ZPBO' ::varchar As intitule, nd_code, nd_comment, geom 
        FROM gracethd.t_noeud WHERE nd_code IN (SELECT nd_code FROM gracethd.t_noeud N WHERE nd_r1_code = 'SADN' AND (Select zp_id from prod.p_zpbo WHERE St_Contains(geom,N.geom)) IS NULL)

        UNION SELECT 'Structure BDD' ::varchar As type,'BAL non raccordée à un câble de raccordement' ::varchar As intitule, nd_code, nd_comment, geom 
        FROM gracethd.t_noeud WHERE nd_code IN (SELECT a.nd_code FROM (SELECT n.nd_code, n.nd_comment, n.geom FROM gracethd.t_noeud n, gracethd.t_suf s 
        WHERE n.nd_code = s.sf_nd_code GROUP BY n.nd_code HAVING count(s.sf_code) < 4 ORDER BY n.nd_code ) AS A 
        LEFT JOIN prod.p_cable c ON ST_DWITHIN(a.geom, ST_EndPoint(c.geom), 0.0001) AND c.cb_code = 26 GROUP BY a.nd_code, a.nd_comment, a.geom 
        HAVING count(c.geom) = 0 ORDER BY nd_code )

        UNION SELECT 'Règle ingénierie' ::varchar As type,'Pavillon (bal entre 1 et 3) dont le nombre de suf est différent du nombre de raccordements' ::varchar As intitule, nd_code, nd_comment, geom 
        FROM gracethd.t_noeud WHERE nd_code IN (SELECT A.nd_code FROM 
        (SELECT n.nd_code, count(s.sf_code) as nb_suf, n.geom FROM gracethd.t_noeud n, gracethd.t_suf s 
        WHERE n.nd_code = s.sf_nd_code GROUP BY n.nd_code HAVING count(s.sf_code) BETWEEN 1 AND 3 ) AS A 
        LEFT JOIN prod.p_cable c ON ST_DWITHIN(A.geom, ST_EndPoint(c.geom), 0.0001) 
        WHERE c.cb_code = 26 GROUP BY A.nd_code, A.nb_suf HAVING count(c.cb_id) <> A.nb_suf)

        UNION SELECT 'Structure BDD' ::varchar As type,'Immeuble (BAL >= 4) dont le nombre de câbles = 0 ou > 1' ::varchar As intitule, nd_code, nd_comment, geom 
        FROM gracethd.t_noeud WHERE nd_code IN (SELECT A.nd_code FROM (SELECT n.nd_code, count(s.sf_code) as nb_suf, n.geom 
        FROM gracethd.t_noeud n, gracethd.t_suf s WHERE n.nd_code = s.sf_nd_code GROUP BY n.nd_code HAVING count(s.sf_code) >= 4 ) AS A 
        LEFT JOIN prod.p_cable c ON ST_DWITHIN(A.geom, ST_EndPoint(c.geom), 0.0001) GROUP BY A.nd_code, A.nb_suf HAVING count(c.cb_id) > 1 OR count(c.cb_id) = 0)

        UNION SELECT 'Topologie' ::varchar As type,'BAL hors ZSRO' ::varchar As intitule, nd_code, nd_comment, geom 
        FROM gracethd.t_noeud N where nd_code NOT IN (Select nd_code from gracethd.t_noeud N2, prod.p_zsro S where St_contains(S.geom, N2.geom))
        ) As tbr
        WHERE ST_Intersects(tbr.geom, (SELECT geom FROM prod.p_zsro WHERE zs_refpm = '""" +  zs_refpm + """'));



        -- verifications for p_sitetech

        DROP TABLE IF EXISTS temp.controle_sitetech_""" +  zs_refpm.split("_")[2] + """;
        CREATE TABLE temp.controle_sitetech_""" +  zs_refpm.split("_")[2] + """ AS
        SELECT row_number() over () id, *
        FROM (
        SELECT 'Structure BDD' ::varchar As type,'Site technique non raccordé à un cable' ::varchar As intitule, st_id, st_comment, geom FROM prod.p_sitetech WHERE st_id NOT IN(SELECT st_id 
        FROM prod.p_sitetech s INNER JOIN prod.p_cable c ON ST_DWITHIN(s.geom, ST_StartPoint(c.geom), 0.0001) )

        UNION SELECT 'Topologie' ::varchar As type,'Doublon géométrie site technique' ::varchar As intitule, st_id, st_comment, geom 
        FROM prod.p_sitetech WHERE st_id IN (SELECT DISTINCT I1.st_id FROM prod.p_sitetech I1 WHERE EXISTS (SELECT * FROM prod.p_sitetech I2 
        WHERE I1.st_id <> I2.st_id AND   St_Dwithin(I1.geom , I2.geom,0.0001)))
        ) As tbr
        WHERE tbr.st_id in (select st_id FROM prod.p_sitetech join prod.p_ltech on st_id = lt_st_code join prod.p_zsro on lt_id = zs_lt_code where zs_refpm = '""" +  zs_refpm + """');



        -- verifications for p_ebp

        DROP TABLE IF EXISTS temp.controle_ebp_""" +  zs_refpm.split("_")[2] + """;
        CREATE TABLE temp.controle_ebp_""" +  zs_refpm.split("_")[2] + """ AS
        SELECT row_number() over () id, *
        FROM (
        -- Note: Exclude les bagguette
        SELECT 'Structure BDD' ::varchar As type,'Boite non associée à un point technique' ::varchar As intitule, bp_id , bp_comment, geom 
        FROM prod.p_ebp WHERE bp_pt_code IS NULL OR bp_pt_code NOT IN ( SELECT pt_id FROM prod.p_ptech)


        UNION SELECT 'Structure BDD' ::varchar As type,'Boite sans câble raccordé (boite apparaissant dans t_ebp mais pas dans t_cable cb_bp1,cb_bp2)' ::varchar As intitule,  bp_id , bp_comment, geom 
        FROM prod.p_ebp WHERE bp_id NOT IN (SELECT cb_bp1 FROM prod.p_cable WHERE cb_bp1 IS NOT NULL UNION SELECT cb_bp2 FROM prod.p_cable WHERE cb_bp2 IS NOT NULL )

        UNION SELECT 'Structure BDD' ::varchar As type,'PBO sans ZPBO' ::varchar As intitule, bp_id , bp_comment, geom 
        FROM prod.p_ebp E WHERE E.bp_typelog = 'PBO' AND (Select zp_id from prod.p_zpbo WHERE St_Contains(geom,E.geom)) IS NULL

        UNION SELECT 'Règle ingenierie' ::varchar As type,'PBO avec cable de capacité superieure ou égale à 288 FO' ::varchar As intitule, bp_id , bp_comment, geom 
        FROM prod.p_ebp WHERE bp_id IN (SELECT distinct e.bp_id FROM prod.p_cable, prod.p_ebp e where (cb_bp1 = e.bp_id or cb_bp2 = e.bp_id) and (cb_capafo >=288)) AND bp_typelog = 'PBO' 

        UNION SELECT 'Topologie' ::varchar As type,'Doublon géométrie boite' ::varchar As intitule, bp_id , bp_comment, geom 
        FROM prod.p_ebp I1 WHERE EXISTS (SELECT * FROM prod.p_ebp I2 WHERE I1.bp_id <> I2.bp_id AND St_Dwithin(I1.geom , I2.geom,0.0001))

        UNION SELECT 'Structure BDD' ::varchar As type,'Boitier immeuble sans point technique immeuble' ::varchar As intitule, bp_id , bp_comment, geom 
        FROM prod.p_ebp WHERE bp_id NOT IN (SELECT bp_id FROM prod.p_ebp E, prod.p_ptech P WHERE E.bp_pttype = 7 AND P.pt_code = 14 AND ST_DWITHIN(E.geom, P.geom,0.0001)) and bp_pttype = 7

        UNION SELECT 'Règle ingenierie' ::varchar As type,'BPE dans zpbo' ::varchar As intitule, bp_id , bp_comment, E.geom 
        FROM prod.p_ebp E, prod.p_zpbo Z WHERE ST_CONTAINS(Z.geom, E.geom) AND bp_typelog = 'BPE'
        ) As tbr
        WHERE ST_Intersects(tbr.geom, (SELECT geom FROM prod.p_zsro WHERE zs_refpm = '""" +  zs_refpm + """'));


        -- verifications for zpbo

        DROP TABLE IF EXISTS temp.controle_zpbo_""" +  zs_refpm.split("_")[2] + """;
        CREATE TABLE temp.controle_zpbo_""" +  zs_refpm.split("_")[2] + """ AS
        SELECT row_number() over () id, *
        FROM (
        SELECT 'Structure BDD' ::varchar As type,'ZPBO sans boitier PBO' ::varchar As intitule, z.zp_id AS zp_id, z.zp_comment, z.geom as geom 
        FROM prod.p_zpbo Z, prod.p_zsro zs WHERE ST_CONTAINS(zs.geom, z.geom) AND (Select count(bp_id) from prod.p_ebp 
        WHERE bp_typelog = 'PBO' AND St_Contains(Z.geom, geom)) = 0 

        UNION SELECT 'Topologie' ::varchar As type,'Doublon de géométrie ZPBO' ::varchar As intitule, I1.zp_id , I1.zp_comment, I1.geom as geom 
        FROM prod.p_zpbo I1, prod.p_zsro zs WHERE EXISTS (SELECT * FROM prod.p_zpbo I2 WHERE I1.zp_id <> I2.zp_id AND I1.geom = I2.geom) 

        UNION SELECT 'Règle ingénierie' ::varchar As type,'ZPBO contenant plus d une BAL dont un immeuble' ::varchar As intitule, c.zp_id, c.zp_comment, c.geom 
        FROM (SELECT A.nd_code, A.nd_comment, A.pavillon, A.zs_refpm, z.zp_id, z.geom , z.zp_comment 
        FROM (SELECT n.nd_code, n.nd_comment, count(s.sf_code) as pavillon, z.zs_refpm, n.geom FROM gracethd.t_noeud n, gracethd.t_suf s, prod.p_zsro z 
        WHERE n.nd_code = s.sf_nd_code AND ST_CONTAINS(z.geom, n.geom) GROUP BY n.nd_code, z.zs_refpm HAVING count(s.sf_code) < 4 ) AS A 
        LEFT JOIN (SELECT zp_id, geom, zp_comment FROM prod.p_zpbo) AS Z ON ST_CONTAINS(z.geom, a.geom) WHERE z.zp_id IS NOT NULL ) AS C 
        WHERE EXISTS (SELECT d.nd_code, d.pavillon, d.zs_refpm, d.zp_id FROM (SELECT A.nd_code, A.pavillon, A.zs_refpm, z.zp_id 
        FROM (SELECT n.nd_code, count(s.sf_code) as pavillon, z.zs_refpm, n.geom FROM gracethd.t_noeud n, gracethd.t_suf s, prod.p_zsro z 
        WHERE n.nd_code = s.sf_nd_code AND ST_CONTAINS(z.geom, n.geom) GROUP BY n.nd_code, z.zs_refpm HAVING count(s.sf_code) >= 4 ) AS A 
        LEFT JOIN (SELECT zp_id, geom FROM prod.p_zpbo) AS Z ON ST_CONTAINS(z.geom, a.geom) WHERE z.zp_id IS NOT NULL ) AS D WHERE c.nd_code <> d.nd_code AND c.zp_id = d.zp_id )

        UNION SELECT 'Règle ingénierie' ::varchar As type,'ZPBO contenant une BPE' ::varchar As intitule, z.zp_id, z.zp_comment, z.geom 
        FROM prod.p_ebp E, prod.p_zpbo Z WHERE ST_CONTAINS(Z.geom, E.geom) AND E.bp_typelog = 'BPE'

        UNION SELECT 'Structure BDD' ::varchar As type,'ZPBO qui a plus d une boite' ::varchar As intitule, z.zp_id, z.zp_comment, z.geom 
        FROM prod.p_ebp E, prod.p_zpbo Z where z.zp_id IN (SELECT z.zp_id FROM prod.p_zpbo z, prod.p_ebp b WHERE ST_CONTAINS(z.geom, b.geom) GROUP BY z.zp_id HAVING COUNT(b.bp_id) > 1)

        ) As tbr
        WHERE tbr.zp_id in ( SELECT zp_id FROM prod.p_zpbo JOIN prod.p_zsro ON zp_zs_code = zs_id WHERE zs_refpm = '""" +  zs_refpm + """');


        -- verifications for p_cable


        DROP TABLE IF EXISTS temp.controle_cable_""" +  zs_refpm.split("_")[2] + """;
        CREATE TABLE temp.controle_cable_""" +  zs_refpm.split("_")[2] + """ AS
        SELECT row_number() over () id, *
        FROM (
        SELECT 'Structure BDD' ::varchar As type,'Câble avec une capacité invalide' ::varchar As intitule, cb_id, cb_comment, geom 
        FROM prod.p_cable WHERE cb_capafo NOT IN (SELECT DISTINCT rc_capafo::integer FROM gracethd.t_refcable ORDER BY rc_capafo::integer)

        UNION SELECT 'Règle ingénierie' ::varchar As type,'Câble avec capa_fo supérieure ou égale à 288 raccordé sur PBO' ::varchar As intitule, cb_id, cb_comment, c.geom 
        FROM prod.p_cable c, prod.p_ebp e WHERE c.cb_capafo >=288 AND bp_typelog = 'PBO' AND (St_Dwithin(St_StartPoint(c.geom),e.geom,0.0001) OR St_Dwithin(St_EndPoint(c.geom),e.geom,0.0001))

        UNION (WITH points AS (SELECT geom FROM prod.p_sitetech UNION ALL SELECT geom FROM prod.p_ebp) SELECT 'Structure BDD' ::varchar As type,
        'Câble sans site technique ou boite en extrémité (vérification géométrique)' ::varchar As intitule, cb_id, cb_comment, c.geom  
        FROM prod.p_cable c LEFT JOIN prod.c_cable ca ON ca.code = c.cb_code LEFT JOIN points  p ON ST_DWITHIN(St_StartPoint(c.geom), p.geom, 0.0001) 
        LEFT JOIN points p2 ON ST_DWITHIN(St_EndPoint(c.geom), p2.geom, 0.0001) WHERE (p.geom IS NULL OR p2.geom IS NULL) and cb_code <> 26)

        UNION SELECT 'Topologie' ::varchar As type,'Doublons géométrie câble (sans les câbles de racco)' ::varchar As intitule, cb_id, cb_comment, geom  
        FROM prod.p_cable I1 WHERE EXISTS (SELECT * FROM prod.p_cable I2 WHERE I1.cb_id <> I2.cb_id AND ST_Equals(I1.geom, I2.geom) AND cb_code <> 26) 

        UNION SELECT 'Topologie' ::varchar As type,'Géométrie non valide du câble' ::varchar As intitule, cb_id, cb_comment, geom  
        FROM prod.p_cable WHERE ST_IsValid(geom) IS NULL

        UNION SELECT 'Topologie' ::varchar As type,'Raccordement qui ne part pas d une boîte ou qui n arrive pas sur un noeud' ::varchar As intitule, cb_id, cb_comment, c.geom  
        FROM prod.p_cable c LEFT JOIN prod.p_ebp e ON ST_DWITHIN(St_StartPoint(c.geom), e.geom, 0.0001) LEFT JOIN gracethd.t_noeud n ON ST_DWITHIN(ST_EndPoint(c.geom), n.geom, 0.0001)  
        WHERE cb_code = 26 AND (e.bp_id IS NULL OR n.nd_code IS NULL)

        UNION SELECT 'Règle ingénierie' ::varchar As type,'Raccordement sur BPE (vérification géométrique)' ::varchar As intitule, cb_id, 
        Case When EXISTS (select cb_id from prod.p_cable where cb_comment = 'BAGUETTE' and St_Intersects (geom,c.geom)) then 'Baguette' Else cb_comment End As cb_comment,c.geom 
        FROM prod.p_cable c LEFT JOIN prod.p_ebp e ON ST_DWITHIN(St_StartPoint(c.geom), e.geom, 0.0001) LEFT JOIN gracethd.t_noeud n ON ST_DWITHIN(ST_EndPoint(c.geom), n.geom, 0.0001) 
        WHERE cb_code = 26 AND e.bp_typelog = 'BPE'

        UNION SELECT 'Règle ingénierie' ::varchar As type,'Raccordement sur BPE (vérification attributaire)' ::varchar As intitule, cb_id, cb_comment, geom 
        FROM prod.p_cable WHERE cb_id IN (select cb_id from prod.p_cable where cb_code = 26 and cb_bp1 IN (Select bp_id from prod.p_ebp where bp_typelog = 'BPE'))

        UNION SELECT 'Règle ingénierie' ::varchar As type,'Raccordement connecté à une mauvaise boîte' ::varchar As intitule, c.cb_id, c.cb_comment, c.geom 
        FROM prod.p_cable c LEFT JOIN prod.p_ltech l ON c.cb_lt_code = l.lt_id LEFT JOIN prod.p_ebp d ON c.cb_bp1 = d.bp_id LEFT JOIN (SELECT n.nd_code, e.bp_id , e.bp_typelog, n.geom 
        FROM gracethd.t_noeud n LEFT JOIN prod.p_zpbo z ON ST_CONTAINS(z.geom, n.geom) LEFT JOIN prod.p_ebp e ON ST_CONTAINS(z.geom, e.geom) 
        WHERE e.bp_typelog = 'PBO' AND n.nd_r1_code = 'SADN') as B ON ST_DWITHIN(ST_EndPoint(c.geom), b.geom, 0.0001) WHERE c.cb_code = 26 AND c.cb_bp1 <> b.bp_id

        UNION SELECT 'Règle ingénierie' ::varchar As type,'Raccordement dont le type logique n est pas raccordement' ::varchar As intitule, cb_id, cb_comment, geom  
        FROM prod.p_cable WHERE cb_code = 26 AND (cb_typelog IS NULL OR cb_typelog <> 'RA')
        ) As tbr
        WHERE tbr.cb_id in (SELECT cb_id FROM prod.p_cable JOIN prod.p_ltech ON cb_lt_code = lt_id JOIN prod.p_zsro ON lt_id = zs_lt_code 
        WHERE zs_refpm = '""" +  zs_refpm + """')
        ;

        """

        try:
            self.executerRequette(query_verify, False)
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))

        self.sendMessageBar(self.success, "Success", "verification is done!", 2)

        # Add the control views as layers to the project
        try:
            self.add_pg_layer("temp", "controle_noeud_" +  zs_refpm.split("_")[2].lower())
            self.add_pg_layer("temp", "controle_sitetech_" +  zs_refpm.split("_")[2].lower())
            self.add_pg_layer("temp", "controle_ebp_" +  zs_refpm.split("_")[2].lower())
            self.add_pg_layer("temp", "controle_zpbo_" +  zs_refpm.split("_")[2].lower())
            self.add_pg_layer("temp", "controle_cable_" +  zs_refpm.split("_")[2].lower())

        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))


        table_names = ['controle_noeud', 'controle_cable', 'controle_ebp', 'controle_zpbo', 'controle_sitetech'  ]

        for table_name in table_names:
            # ------------- style the control layers --------------
            try:
                # get the layer
                layer = QgsMapLayerRegistry.instance().mapLayersByName(table_name + '_' + zs_refpm.split("_")[2].lower())[0]
                self.add_style(layer)

            except Exception as e:
                self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))

            #------------------------------------------------------

            # verify if the control tables have records and notify the user
            the_query = 'SELECT * FROM temp.' + table_name + '_' + zs_refpm.split("_")[2].lower()
            result = self.executerRequette(the_query, True)
            if result is None:
                pass

            elif len(result) >= 1:
                # self.fenetreMessage(QMessageBox.Warning,"Warning", "Consultz la table : " + table_name + '_' + zs_refpm.split("_")[2].lower())
                self.sendMessageBar(self.info, "Info", 'Consultz la table : <b style="color:#007E33;">' + table_name + '_' + zs_refpm.split("_")[2].lower() + "</b>", 1.5)






    def add_style(self, layer):
        """ Style a qgis layer by classifying the features using the 'intitule' field and giving the classes random colors """

        from random import randrange

        # get unique values 
        fni = layer.fieldNameIndex('intitule')
        unique_values = layer.dataProvider().uniqueValues(fni)

        # define categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol = QgsSymbolV2.defaultSymbol(layer.geometryType())

            # configure a symbol layer
            layer_style = {}
            layer_style['color'] = '%d, %d, %d' % (randrange(0,256), randrange(0,256), randrange(0,256))

            # Define the style of the point layers
            if layer.wkbType()==QGis.WKBPoint:
                layer_style['color'] = '%d, %d, %d' % (randrange(0,256), randrange(0,256), randrange(0,256))
                layer_style['size'] = '2'
                symbol_layer = QgsSimpleMarkerSymbolLayerV2.create(layer_style)
                symbol_layer.setOutlineWidth(0)

            # Define the style of the lineString layers
            if layer.wkbType()==QGis.WKBLineString:
                # print 'Layer is a line layer'
                layer_style['width_border'] = '0.46'
                layer_style['size'] = '0.46'
                symbol_layer = QgsSimpleFillSymbolLayerV2.create(layer_style)

            # Define the style of the polyon layers
            if layer.wkbType()==QGis.WKBPolygon or layer.wkbType()==QGis.WKBMultiPolygon:
                # print 'Layer is a polygon layer'
                layer_style['width_border'] = '0.46'
                layer_style['color_border'] = 'black'
                symbol_layer = QgsSimpleFillSymbolLayerV2.create(layer_style)



            symbol_layer = QgsSimpleFillSymbolLayerV2.create(layer_style)

            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)

            # create renderer object
            category = QgsRendererCategoryV2(unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)

        # create renderer object
        renderer = QgsCategorizedSymbolRendererV2('intitule', categories)

        # assign the created renderer to the layer
        if renderer is not None:
            layer.setRendererV2(renderer)

        # layer.rendererChanged.connect(self.changed_renderer)
        layer.triggerRepaint()




    def add_pg_layer(self, schema, table_name):
        ''' Adds a postgres geometry table as a layer to the QGIS project'''

        # Create a data source URI
        uri = QgsDataSourceURI()

        # set host name, port, database name, username and password
        uri.setConnection(self.dlg.lineEdit_Host.text(), "5432", self.dlg.lineEdit_BD.text(), self.dlg.lineEdit_User.text(), self.dlg.lineEdit_Password.text())

        # set database schema, table name, geometry column and optionally subset (WHERE clause)
        uri.setDataSource(schema, table_name, "geom")

        vlayer = QgsVectorLayer(uri.uri(False), table_name, "postgres")


        # Check first if the layer is already added to the map
        layer_names = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
        if table_name not in layer_names:
            # Add the vector layer to the map
            QgsMapLayerRegistry.instance().addMapLayers([vlayer])
            self.sendMessageBar(self.info, "Info", 'Layer <b style="color:#007E33;"> %s </b> is loaded' % vlayer.name(), 2)

        else :
            self.sendMessageBar(self.info, "Info", 'Layer <b style="color:#007E33;"> %s </b> already exists but it has been updated' % vlayer.name(), 2)




    def calcul_orientation_cable(self):
        ''' Determines the orientation of the cables within the table p_cable. Should not be used unless
        we had many errors when testing the orientation using "verify_orientation_cable()" '''

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()      


        # self.create_cable_cluster(zs_refpm)
        # query to update the cables' geometry. The objective is to inhance the orientation of the cables, but we still need to verify that in the next step

        query_orientation = """
        UPDATE prod.p_cable
        SET geom = A.geom
        FROM (
        SELECT cb_id, St_LineMerge(St_Union(ARRAY(Select geom from prod.p_cheminement where cm_id IN (select dm_cm_id from prod.p_cond_chem 
        where dm_cd_id IN (select cc_cd_id from prod.p_cab_cond where cc_cb_id = p.cb_id))))) as geom
        FROM prod.p_cable p
        WHERE cb_lt_code = (SELECT zs_lt_code FROM prod.p_zsro WHERE zs_refpm = '""" + zs_refpm + """' ) AND p.cb_comment IS NULL AND cb_typelog = 'DI' -- Paramétrer cb_lt_code selon SRO
        ) AS A
        WHERE prod.p_cable.cb_id = A.cb_id

        """

        try:
            self.executerRequette(query_orientation, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)




    def create_cable_cluster(self, zs_refpm):


        query_cluster = """

                        DO
                        $$
                        DECLARE
                        id record ;
                        nro record ;
                        counter integer = 1 ;
                        counter2 integer = 1 ;


                        BEGIN

                            DROP TABLE IF EXISTS temp.cb_cluster_""" + zs_refpm.split("_")[2] + """;
                            CREATE TABLE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ (gid serial, this_id integer, cb_code integer,  cb_lt_code integer, cb_r3_code varchar, rang integer, 
                            hierarchie varchar, passage integer, etiquette varchar(254), geom Geometry(Linestring,2154));    
                            CREATE INDEX cb_cluster_""" + zs_refpm.split("_")[2] + """_geom_gist ON temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ USING GIST (geom); 
                            
                            FOR nro IN (SELECT c.cb_id, c.cb_code,c.cb_lt_code, c.geom, s.st_nom FROM temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """ c, prod.p_sitetech s 
                            WHERE ST_INTERSECTS(c.geom, s.geom) AND st_id = (SELECT lt_st_code FROM prod.p_ltech WHERE lt_etiquet LIKE '%""" + zs_refpm.split("_")[2] + """')
                             AND c.cb_lt_code = (SELECT zs_lt_code FROM prod.p_zsro WHERE zs_refpm = '""" + zs_refpm + """' )) 
                            LOOP -- Vérifier site technique
                            
                            INSERT INTO temp.cb_cluster_""" + zs_refpm.split("_")[2] + """(this_id, cb_code, cb_lt_code, cb_r3_code, rang, hierarchie, geom)   
                            SELECT nro.cb_id, nro.cb_code, nro.cb_lt_code, nro.st_nom, counter, CONCAT(counter, '.',counter2), nro.geom;

                            counter2 = counter2 + 1;

                            END LOOP;

                            FOR id IN (SELECT cb_id FROM temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """ WHERE cb_code <> 26)

                            LOOP
                            
                            counter = counter + 1;
                            
                            INSERT INTO temp.cb_cluster_""" + zs_refpm.split("_")[2] + """(this_id, cb_code, cb_lt_code, cb_r3_code, rang, hierarchie, passage, geom)
                            SELECT c.cb_id, c.cb_code, l. cb_lt_code, l. cb_r3_code, counter, CONCAT(counter,'.',
                            ROW_NUMBER() OVER(PARTITION BY l.hierarchie ORDER BY ST_X(ST_EndPoint(ST_INTERSECTION(ST_BUFFER(ST_STARTPOINT(c.geom), 1), c.geom)))),'.', l.hierarchie) as hierarchie, 
                                CASE WHEN ST_Touches(c.geom, St_EndPoint(l.geom)) AND c.cb_code = l.cb_code AND l.passage IS NULL THEN l.this_id 
                                     WHEN ST_Touches(c.geom, St_EndPoint(l.geom)) AND c.cb_code = l.cb_code AND l.passage IS NOT NULL THEN l.passage END as test, c.geom
                            FROM temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """ c, temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ l
                            WHERE l.rang = (counter - 1) AND St_Touches(c.geom, St_EndPoint(l.geom)) AND c.cb_id NOT IN (SELECT this_id FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """) 
                            AND c.cb_code <> 26 
                            ORDER BY ST_X(ST_EndPoint(ST_INTERSECTION(ST_BUFFER(ST_STARTPOINT(c.geom), 1), c.geom)));

                            
                            END LOOP;

                            DELETE FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ WHERE gid IN (
                                            SELECT gid--, this_id, quantite
                                            FROM (
                                                SELECT gid, this_id, ROW_NUMBER() OVER(PARTITION BY this_id ORDER BY this_id) as quantite
                                                FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                                                WHERE this_id IN (SELECT this_id FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ GROUP BY this_id HAVING count(this_id) > 1)
                                                ) AS A 
                                            WHERE quantite > 1
                                            ORDER BY this_id
                                            );

                            UPDATE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                            SET passage = A.this_id
                            FROM (
                                SELECT this_id, cb_code, geom
                                FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ WHERE this_id IN (SELECT passage FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """) AND passage IS NULL 
                                ) AS A
                            WHERE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """.this_id = A.this_id;

                            UPDATE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                            SET passage = NULL
                            WHERE this_id IN (
                                        SELECT this_id--, rang, hierarchie, passage
                                        FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ c, prod.p_ebp e
                                        WHERE ST_DWITHIN(St_EndPoint(c.geom), e.geom, 0.0001) AND passage IS NOT NULL AND e.bp_pttype = 7
                                        );

                            UPDATE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                            SET passage = NULL
                            WHERE passage IN (
                                        SELECT passage--, count(passage)
                                        FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                                        WHERE passage IS NOT NULL
                                        GROUP BY passage
                                        HAVING count(passage) = 1
                                    );

                            UPDATE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                            SET passage = A.this_id
                            FROM (
                                SELECT this_id, cb_code--, geom
                                FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ WHERE passage IS NULL 
                                ) AS A
                            WHERE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """.this_id = A.this_id;


                            /*UPDATE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                            SET etiquette = B.etiquette
                            FROM ( 

                                SELECT *, CONCAT(nom, insee, '_', quadri, '_', (plage + taux), partie) as etiquette
                                FROM (
                                    SELECT c1.this_id, c1.cb_code, c1.cb_lt_code, c1.cb_r3_code, c1.rang, c1.hierarchie, c1.passage as id_passage, c2.rang as rang_passage, c2.hierarchie as ordre_passage,
                                        CASE WHEN c1.this_id IN (SELECT this_id FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ c, 
                                        prod.p_ebp e WHERE ST_DWITHIN(St_EndPoint(c.geom), e.geom, 0.0001) AND passage IS NOT NULL AND e.bp_pttype = 7) THEN 'CFI'
                                             ELSE 'CDI' END as nom,
                                        (SELECT LEFT(c.insee, 2) FROM cadastre.communes c, prod.p_sitetech s WHERE ST_CONTAINS(c.geom, s.geom) AND st_id = 2) as insee, c3.quadri, -- Vérifier SRO
                                        4000 + DENSE_RANK () OVER (PARTITION BY RIGHT(c2.hierarchie, 3) ORDER BY c2.rang, c1.passage, LEFT(c2.hierarchie, 50) ) as plage, 
                                        CASE WHEN RIGHT(c1.hierarchie, 3) LIKE '1.1' THEN 100 ELSE 200 END as taux,
                                        CASE WHEN c2.passage IN ( SELECT passage FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ GROUP BY passage HAVING count(passage) > 1 ) THEN
                                         CONCAT('-', ROW_NUMBER() OVER(PARTITION BY c2.passage ORDER BY RIGHT(c2.hierarchie, 3),  c2.rang, LEFT(c2.hierarchie, 50), RIGHT(c1.hierarchie, 3),  c1.rang, LEFT(c1.hierarchie, 50) ))
                                             ELSE NULL END as partie
                                    FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ c1
                                    LEFT JOIN temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ c2 ON c2.this_id = c1.passage
                                    LEFT JOIN (SELECT SUBSTRING(b.ba_etiquet, 11,4)::varchar as quadri, c4.hierarchie FROM temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """ ca , temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ c4, prod.p_baie b WHERE b.ba_id = ca.cb_ba1 AND c4.this_id = ca.cb_id AND ca.cb_ba1 IS NOT NULL) c3 ON c3.hierarchie = RIGHT(c1.hierarchie, 3)
                                    ORDER BY RIGHT(c2.hierarchie, 3),  c2.rang, LEFT(c2.hierarchie, 50), RIGHT(c1.hierarchie, 3),  c1.rang, LEFT(c1.hierarchie, 50) 
                                    ) AS A
                                ) AS B
                            WHERE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """.this_id = B.this_id;


                            UPDATE temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """
                            SET cb_etiquet = B.etiquette,
                                cb_lt_code = B.cb_lt_code,
                                cb_r3_code = B.cb_r3_code
                            FROM (
                                SELECT * 
                                FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                                 ) as B
                            WHERE temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """.cb_id = b.this_id;*/
                            
                        END;
                        $$ language plpgsql;
        

        """


        try:
            self.executerRequette(query_cluster, False)
            # self.fenetreMessage(QMessageBox, "info", "The table cb_cluster is created")

        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)




    def verify_orientation_cable(self):
        """ Look for errors that indicate problems with the orientation of the cables within p_cable """

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()



        query = """
                DROP TABLE IF EXISTS temp.controle_ebp_pour_orientation_""" +  zs_refpm.split("_")[2] + """;
                CREATE TABLE temp.controle_ebp_pour_orientation_""" +  zs_refpm.split("_")[2] + """ AS
                SELECT row_number() over () id, *
                FROM (
                    SELECT 'Structure BDD' ::varchar As type,'Boite sans câble entrant' ::varchar As intitule, bp_id , bp_comment, geom from prod.p_ebp  
                    WHERE bp_id NOT IN (SELECT cb_bp2 FROM prod.p_cable WHERE cb_code <> 26 AND cb_bp2 IS NOT NULL) 

                    UNION SELECT 'Structure BDD' ::varchar As type,'Boite sans câble sortant' ::varchar As intitule, bp_id , bp_comment, geom from prod.p_ebp  
                    WHERE bp_pttype <> 7 AND bp_id NOT IN (SELECT cb_bp1 FROM prod.p_cable WHERE cb_bp1 IS NOT NULL) AND (bp_comment IS NULL OR bp_comment <> 'BAGUETTE')

                    UNION SELECT 'Structure BDD' ::varchar As type,'Boite ayant plusieurs câbles entrant' ::varchar As intitule, bp_id , bp_comment, prod.p_ebp.geom FROM prod.p_ebp, prod.p_cable 
                    WHERE bp_id = cb_bp2 AND cb_code <> 26 GROUP BY bp_id HAVING COUNT(cb_id) > 1 
                ) As tbr          
                WHERE ST_Intersects(tbr.geom, (SELECT geom FROM prod.p_zsro WHERE zs_refpm = '""" +  zs_refpm + """'));
        """

        self.executerRequette(query, False)

        # Add the table that contains the errors to the map canvas to be examined by the user
        self.add_pg_layer("temp", "controle_ebp_pour_orientation_" +  zs_refpm.split("_")[2].lower())

        # Enable the button of the orientation of the cables in case the user found many errors during the verification step
        self.dlg.findChild(QPushButton, "pushButton_orientation").setEnabled(True)





    def create_temp_cable_table(self, zs_refpm):
        ''' Create a copy of prod.p_cable to use it for the calcualtions
            zs_refpm : an identifyer for the zones SRO selected by the user
         '''
        query = """ DROP TABLE IF EXISTS temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """;
                CREATE TABLE temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """ 
                as (SELECT cable.* FROM prod.p_cable as cable JOIN prod.p_ltech ON cb_lt_code = lt_id JOIN prod.p_zsro ON lt_id = zs_lt_code 
                WHERE zs_refpm = '""" + zs_refpm + """' AND cb_typelog = 'DI');

                -- Add a column that will hold the values of fb_util
                ALTER TABLE temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ ADD COLUMN cb_fo_util integer;
                ALTER TABLE temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ ADD COLUMN capa_fo_util integer;
                ALTER TABLE temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ ADD COLUMN passage BOOLEAN DEFAULT FALSE;

        """

        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)


    def calcul_fibres_utiles(self):
        ''' Calculate the number of fibers per cable and save the results in the working table cable_pour_boite_* 
        (*) : is the quadrigram of the selected zone ZSRO '''


        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()        
        self.create_temp_cable_table(zs_refpm)
        
        # Create cable cluster to use it in the calculation of fb_util
        try:
            self.create_cable_cluster(zs_refpm)

        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning, "Erreur_fenetreMessage", str(e))


        self.add_pg_layer("temp", "cb_cluster_" + zs_refpm.split("_")[2].lower())

        # Create the query that calculates fb_util
        
        query = """
                DO
                $$
                DECLARE
                counter integer = 1 ;
                rang_fibre integer;
                id record ;
                id2 record ;
                sro text ;
                base text;
                typelog text = 'PBO';

                BEGIN


                sro = '""" + zs_refpm.split("_")[2] + """'; ---entrez le SRO


                EXECUTE 'DROP TABLE IF EXISTS temp.p_cable_' || sro;
                EXECUTE 'CREATE TABLE temp.p_cable_' || sro || '(gid serial, rang integer, this_id integer, fo_util integer, reserve integer, geom Geometry(Linestring,2154))';
                ALTER TABLE temp.p_cable_""" + zs_refpm.split("_")[2] + """ ADD PRIMARY KEY (gid);
                CREATE INDEX ON temp.p_cable_""" + zs_refpm.split("_")[2] + """ USING GIST(geom); 
                EXECUTE 'INSERT INTO temp.p_cable_' || sro || '(this_id, rang, geom) SELECT this_id, rang, geom from temp.cb_cluster_' || sro;

                --------------------------------------------------------------------------------------

                EXECUTE 'UPDATE temp.p_cable_' || sro || '
                
                     SET fo_util = (Case when fo_util IS NOT NULL then fo_util else 0 End) + B.nbfibre,
                     reserve = (Case when temp.p_cable_' || sro || '.reserve IS NOT NULL then temp.p_cable_' || sro || '.reserve else 0 End) + B.reserve
                     FROM (
                        SELECT c.cb_id as this_id, bp.zp_nbfibre as nbfibre, bp.zp_reserve as reserve
                        FROM temp.cable_pour_boite_' || sro || ' c 

                     LEFT JOIN (
                                SELECT bp_id, zp_id, zp_nbfibre, zp_reserve, prod.p_ebp.geom
                                FROM prod.p_ebp
                                join prod.p_zpbo on bp_id = zp_bp_code
                                where bp_typelog = ' || quote_literal(typelog) || '
                     ) as bp

                    ON ST_DWithin(St_EndPoint(c.geom), bp.geom, 0.0001)
                     WHERE bp.zp_nbfibre IS NOT NULL
                     ) AS B
                     WHERE temp.p_cable_' || sro || '.this_id = B.this_id';


                -------------------------------- New part developped by Kevin ---------------------------


                /*EXECUTE ' UPDATE temp.p_cable_' || sro || '
                        SET fo_util = A.zd_fo_util,
                            reserve = A.reserve  --------- new 2 --------

                        FROM (
                            SELECT f.this_id, zd_fo_util, 
                            (SUM(f2.reserve) + (Case when z.zd_fo_util IS NOT NULL then z.zd_fo_util else 0 End)) as reserve ------------------- new 3 -----------------------
                            FROM temp.p_cable_' || sro || ' f
                            LEFT JOIN temp.p_cable_' || sro || ' f2 ON ST_DWITHIN(ST_EndPoint(f.geom), ST_StartPoint(f2.geom), 0.0001)
                            LEFT JOIN prod.p_ebp e ON ST_DWITHIN(ST_EndPoint(f.geom), e.geom, 0.0001)
                            LEFT JOIN prod.p_zdep z ON e.bp_id = z.zd_r6_code
                            WHERE f2.this_id IS NULL AND e.bp_id IS NOT NULL AND e.bp_pttype <> 7
                            GROUP BY f.this_id, f.rang, z.zd_fo_util
                            ORDER BY f.this_id
                            ) AS A
                        WHERE temp.p_cable_' || sro || '.this_id = A.this_id';*/


                --------------------------------------------------------------------------------------------


                DROP TABLE IF EXISTS temp.p_cable_tbr;
                CREATE TABLE temp.p_cable_tbr (gid serial, rang integer, this_id integer, fo_util integer, reserve integer, geom Geometry(Linestring,2154));
                EXECUTE 'INSERT INTO temp.p_cable_tbr SELECT * FROM temp.p_cable_' || sro; 

                    For id in (Select gid from temp.p_cable_tbr -- WHERE fo_util IS NULL 
                    order by rang DESC) loop
                        ------------ test part ------------------
                        EXECUTE 'UPDATE temp.p_cable_' || sro || ' c SET fo_util = COALESCE(fo_util, 0) + 
                        (COALESCE((SELECT SUM(COALESCE(c2.fo_util, 0)) FROM temp.p_cable_' || sro || ' c2 WHERE ST_Dwithin(St_StartPoint(c2.geom), St_EndPoint(c.geom),0.0001)), 0)),
                        reserve = COALESCE(c.reserve, 0) + 
                        (COALESCE((SELECT SUM(COALESCE(c2.reserve, 0)) FROM temp.p_cable_' || sro || ' c2 WHERE ST_Dwithin(St_StartPoint(c2.geom), St_EndPoint(c.geom),0.0001)), 0))                        WHERE c.gid = $1' USING id.gid;
                    END LOOP;


                    -----------------------------------------
                     /* EXECUTE 'UPDATE temp.p_cable_' || sro || ' c SET fo_util = (Case when fo_util IS NOT NULL then fo_util else 0 End) + (Select (SUM(c2.fo_util) + (Case when (Select SUM(z.zd_fo_util)
                     FROM prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) IS NOT NULL 
                     THEN (Select SUM(z.zd_fo_util) from prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) else 0 End )) As fo_util 
                     FROM temp.p_cable_' || sro || ' c2 WHERE ST_Dwithin(St_StartPoint(c2.geom),St_EndPoint(c.geom),0.0001)),
                     reserve = (Select (SUM(c2.reserve) + (Case when (Select SUM(z.zd_fo_util)
                     FROM prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) IS NOT NULL 
                     THEN (Select SUM(z.zd_fo_util) from prod.p_ebp e LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) ) else 0 End )) As fo_util 
                     FROM temp.p_cable_' || sro || ' c2 WHERE ST_Dwithin(St_StartPoint(c2.geom),St_EndPoint(c.geom),0.0001))

                     WHERE c.gid = $1' USING id.gid;
                     --EXECUTE 'UPDATE temp.p_cable_' || sro || ' c SET fo_util = (Select (SUM(c2.fo_util) + (Case when z.zd_fo_util IS NOT NULL then z.zd_fo_util else 0 End)) As fo_util FROM temp.p_cable_' || sro || ' c2 LEFT JOIN prod.p_ebp e ON ST_Dwithin(e.geom,St_EndPoint(c.geom),0.0001) LEFT JOIN prod.p_zdep z ON e.bp_id = zd_r6_code WHERE ST_Dwithin(St_StartPoint(c2.geom),St_EndPoint(c.geom),0.0001) GROUP BY z.zd_fo_util) WHERE c.gid = $1' USING id.gid;
                    END LOOP;*/


                --------------------------------------------------------------------------------------


                EXECUTE 'UPDATE temp.cable_pour_boite_' || sro || ' SET cb_fo_util = temp_cable.reserve FROM temp.p_cable_' || sro || ' AS temp_cable WHERE cb_id = temp_cable.this_id';
                    
                DROP TABLE IF EXISTS temp.p_cable_tbr;
                                        
                END;
                $$ language plpgsql;


        """
        self.executerRequette(query, False)

        self.find_passage(zs_refpm)
        self.cb_code_to_fo_util(zs_refpm)
        self.add_pg_layer("temp", "cable_pour_boite_" + zs_refpm.split("_")[2].lower())



    def find_passage(self, zs_refpm):
        ''' Determin if the cable is of type "passage" based on the etiquets of the cables '''

        query = """
        UPDATE temp.cable_pour_boite_""" + zs_refpm.split("_")[2] + """ SET passage = true
        WHERE cb_etiquet like '%-%';
        """

        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)



    def calcul_boite_dimensions(self):
        ''' Execute all the steps necessary to calculate the dimensions (types and zises) of the boites optiques '''

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        self.create_temp_boite_table(zs_refpm)
        self.calcul_nb_cassettes_max(zs_refpm)
        self.calcul_nb_epissures(zs_refpm)
        self.calcul_nb_cassettes_max(zs_refpm)
        self.calcul_nb_cassettes(zs_refpm)
        self.calcul_type_boite(zs_refpm)
        self.add_pg_layer("temp", "ebp_" + zs_refpm.split("_")[2].lower())




    def create_temp_boite_table(self, zs_refpm):
        ''' Make a working copy of the table p_ebp to use it for the calcualtions'''

        query = """DROP TABLE IF EXISTS temp.ebp_""" + zs_refpm.split("_")[2].lower() + """;
                CREATE TABLE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS SELECT * FROM prod.p_ebp
                WHERE bp_zs_code = '""" + zs_refpm.split("_")[2] + """';

                CREATE INDEX ON temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ USING GIST(geom);
                ALTER TABLE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ ADD PRIMARY KEY (bp_id);


                ALTER TABLE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ ADD COLUMN capa_amnt_fo_util INT, ADD COLUMN zp_reserve INT DEFAULT 0, ADD COLUMN nb_epissures INT,
                ADD COLUMN nb_cassettes_epissure INT DEFAULT 0, ADD COLUMN nb_cassettes_reserve INT DEFAULT 0, ADD COLUMN nb_cassettes_max INT DEFAULT 999, ADD COLUMN nb_cassettes_total INT DEFAULT 0;

        """

        try:
            self.executerRequette(query, False)
            self.sendMessageBar(self.info, "Info", "The table temp.ebp_"  + zs_refpm.split("_")[2] + " is created", 2)

        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)





    def cb_code_to_fo_util(self, zs_refpm):
        ''' Calculate the number of fibres utiles (fo_util) per cable based on the type (cb_code) of the cable '''
        query = """UPDATE temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ SET capa_fo_util = case
                WHEN cb_code in (1, 12, 19, 27) THEN 12
                WHEN cb_code in (2, 13, 20, 28) THEN 24
                WHEN cb_code in (29) THEN 36
                WHEN cb_code in (3, 14, 21, 30) THEN 48
                WHEN cb_code in (4, 15, 22, 31) THEN 72
                WHEN cb_code in (5, 16, 23, 32) THEN 96
                WHEN cb_code in (6, 17, 24, 33) THEN 144
                WHEN cb_code in (7, 18, 25, 34) THEN 288
                WHEN cb_code in (8) THEN 432
                WHEN cb_code in (9) THEN 576
                WHEN cb_code in (10) THEN 720
                WHEN cb_code in (11) THEN 864
                END;
        """

        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)


    def calcul_nb_epissures(self, zs_refpm):
        ''' Calculate the number of "epissures" per boite '''

        self.create_intermediate_table(zs_refpm)

        query1 = """ -- upddate the field zp_reserve in the table temp.ebp_*
                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp 
                SET zp_reserve = zpbo.zp_reserve
                FROM prod.p_zpbo as zpbo
                WHERE ebp.bp_id = zpbo.zp_bp_code;

        """
        try:
            self.executerRequette(query1, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)




        query2_old = """-- first case : passage
                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET 
                        nb_epissures = sub1.nb_epissures
                        -- take the minimum value between the sum of the values of the cables that depart except passage, and the capacity of the cable that enters the boite
                        FROM (SELECT bp_id, LEAST(sum(c1.cb_fo_util), avg(c2.capa_fo_util)::int) as nb_epissures
                            from temp.ebp_maz1 as bp
                            -- join the cables that depart from the boite
                            join temp.cable_pour_boite_maz1 c1
                            on st_dwithin(bp.geom, st_startpoint(c1.geom), 0.0001)
                            -- join the cables that enter into the boite
                            join temp.cable_pour_boite_maz1 c2
                            on st_dwithin(bp.geom, st_endpoint(c2.geom), 0.0001)
                            where c2.passage and ((not c1.passage) or (c1.cb_code <> c2.cb_code))
                            group by bp_id) sub1
                WHERE ebp.bp_id = sub1.bp_id;




                --UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET 
                        --nb_epissures = sub2.nb_epissures
                        /*FROM (
                            SELECT bp_id, LEAST(sum(c.cb_fo_util), avg(c2.capa_fo_util)::int) AS nb_epissures
                             from temp.ebp_maz1 as bp
                            -- join with the cables that depart from the boite
                            join temp.cable_pour_boite_maz1 c
                            on st_dwithin(bp.geom, st_startpoint(c.geom), 0.0001)
                            -- join with the cable that enter the boite
                            join temp.cable_pour_boite_maz1 c2
                            on st_dwithin(bp.geom, st_endpoint(c2.geom), 0.0001)
                            where not c2.passage and nb_epissures is NULL
                            group by bp_id, c2.capa_fo_util) sub2
                        WHERE ebp.bp_id = sub2.bp_id;*/
            """



        query2 = """
                -- refresh p_zpbo
                UPDATE prod.p_zpbo SET zp_comment = zp_comment;


                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                nb_epissures = ebp.zp_reserve;


                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                nb_epissures = ebp.nb_epissures + COALESCE(sub.nb_epissures, 0)
                -- take the minimum value between the sum of the values of the cables that depart except passage, and the capacity of the cable that enters the boite
                FROM (SELECT non_passage.bp_id as bp_id, COALESCE(sum(non_passage.cb_fo_util), 0) as nb_epissures
                    FROM (SELECT ebp2.bp_id as bp_id, COALESCE(c.cb_fo_util, 0) as cb_fo_util
                            FROM temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp2
                            LEFT JOIN temp.ebp_cable_""" + zs_refpm.split("_")[2].lower() + """ AS ebp_cable
                            ON ebp2.bp_id = ebp_cable.bp_id
                            LEFT JOIN temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ AS c
                            ON c.cb_id = ebp_cable.cb_id
                            WHERE ebp_cable.entree_sortie = 's' AND NOT ebp_cable.passage) AS non_passage
                            GROUP BY non_passage.bp_id) AS sub
                WHERE ebp.bp_id = sub.bp_id;


                -- compare the value in nb_epissures and the capacity of the cable and take the least between them
                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                nb_epissures = LEAST(ebp.nb_epissures, c.capa_fo_util), capa_amnt_fo_util = c.capa_fo_util
                FROM temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS bp
                JOIN temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ AS c
                ON st_dwithin(bp.geom, st_endpoint(c.geom), 0.0001)
                WHERE ebp.bp_id = bp.bp_id;


        """



        try:
            self.executerRequette(query2, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)

        # self.fenetreMessage(QMessageBox, "info", "The query is executed")
        



    def create_intermediate_table(self, zs_refpm):

        query = """DROP TABLE IF EXISTS temp.ebp_cable_""" + zs_refpm.split("_")[2].lower() + """;
                CREATE TABLE temp.ebp_cable_""" + zs_refpm.split("_")[2].lower() + """ as
                SELECT bp_id, cb_id, 's' AS entree_sortie, false as passage
                FROM temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ as bp
                JOIN temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ as c
                ON c.cb_bp1 = bp.bp_id
                UNION 
                SELECT bp_id, cb_id, 'e' AS entree_sortie, false as passage
                from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ as bp
                JOIN temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ as c
                ON c.cb_bp2 = bp.bp_id
                ORDER BY bp_id, entree_sortie;


                UPDATE temp.ebp_cable_""" + zs_refpm.split("_")[2].lower() + """ SET passage = true
                WHERE (bp_id, cb_id) IN (select distinct tempo.bp_id, tempo.cb_id
                FROM temp.ebp_cable_""" + zs_refpm.split("_")[2].lower() + """ as tempo, temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ as c1, 
                temp.cable_pour_boite_""" + zs_refpm.split("_")[2].lower() + """ AS c2
                WHERE split_part(c1.cb_etiquet, '-', '1') = split_part(c2.cb_etiquet, '-', '1')
                AND c1.cb_etiquet <> c2.cb_etiquet
                AND (c1.cb_bp1 = tempo.bp_id OR c1.cb_bp2 = tempo.bp_id)
                AND (c2.cb_bp1 = tempo.bp_id OR c2.cb_bp2 = tempo.bp_id)
                AND (tempo.cb_id = c1.cb_id OR tempo.cb_id = c2.cb_id));

        """



        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)




    def calcul_nb_cassettes_max(self, zs_refpm):
        ''' Calcualte the maximum possible number of fibers for the specified boite '''

        query = """UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                nb_cassettes_max = CASE
                WHEN capa_amnt_fo_util = 12 THEN 1
                WHEN capa_amnt_fo_util = 24 THEN 2
                WHEN capa_amnt_fo_util = 48 THEN 4
                WHEN capa_amnt_fo_util = 72 THEN 6
                WHEN capa_amnt_fo_util = 96 THEN 8
                WHEN capa_amnt_fo_util = 144 THEN 12
                END
                WHERE bp_typelog = 'PBO'

        """
        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)




    def calcul_nb_cassettes(self, zs_refpm):
        ''' Calculate the number of cassettes (epissure, reserve, and total) per boite '''

        query = """UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                nb_cassettes_epissure = ceiling(ebp.nb_epissures / 12.0), nb_cassettes_reserve = ceiling((capa_amnt_fo_util / 12.0) * 0.3);

                -- add one cassette to the reserve in the case of BPE and capa_amnt_fo_util <= 144
                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                nb_cassettes_reserve = nb_cassettes_reserve + 1
                WHERE bp_typelog = 'BPE' AND capa_amnt_fo_util <= 144;

                -- calculate nb_cassettes_total
                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                nb_cassettes_total = LEAST(nb_cassettes_max, nb_cassettes_epissure + nb_cassettes_reserve);

        """


        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)


    def calcul_type_boite(self, zs_refpm):
        ''' Determine the type (bp_model) of the boite based on the total number of cassettes (nb_cassettes_total) and the type of the point technique (bp_pttype) '''

        query = """UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                bp_model = 8;



                UPDATE temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ AS ebp SET
                    bp_model = CASE
                    WHEN nb_cassettes_total <= 4 AND bp_pttype in (2, 3, 5, 6, 7) THEN 1
                    WHEN nb_cassettes_total > 4 AND nb_cassettes_total <= 12 and bp_pttype in (2, 3, 5, 6, 7) THEN 2
                    WHEN nb_cassettes_total > 12 AND nb_cassettes_total <= 24 THEN 5
                    WHEN nb_cassettes_total <= 4 AND bp_pttype in (1, 4) THEN 3
                    WHEN nb_cassettes_total > 4 AND nb_cassettes_total <= 12 AND bp_pttype in (1, 4) THEN 4
                    WHEN nb_cassettes_total > 24 AND nb_cassettes_total <= 56 AND bp_pttype in (1, 4) THEN 6
                    WHEN nb_cassettes_total > 56 AND nb_cassettes_total <= 80 AND bp_pttype in (1, 4) THEN 7
                    END;

        """

        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)




    def verify_capacite_chambre(self):
        ''' Compare the type of each chamber with the types of the boites within it to determine if the chambre can be occupied by boites of these types or not.
        Create a temporary table to hold the errors and add it to the project. '''

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        define_function = """CREATE OR REPLACE FUNCTION temp.occupation_chambres(varchar, integer, integer, integer, integer, varchar)
                          RETURNS void AS
                                $BODY$
                                DECLARE
                                enreg record ;
                                counter1 integer;
                                counter2 integer;
                                counter3 integer;
                                counter4 integer;

                                BEGIN

                                FOR enreg IN (SELECT * FROM prod.p_ptech where pt_nature = $1 AND pt_zs_code = $6)
                                LOOP

                                counter1 = (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e 
                                where enreg.pt_id = e.bp_pt_code AND bp_model = 3) + (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e, 
                                prod.p_ptech p, prod.p_cable c where e.bp_pttype = 8 and p.pt_id = enreg.pt_id and St_Dwithin(e.geom, St_EndPoint(c.geom),0.0001) and St_Dwithin(p.geom, St_StartPoint(c.geom),0.0001) AND bp_model = 3);

                                counter2 = (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e 
                                where enreg.pt_id = e.bp_pt_code AND bp_model IN (1,2,4)) + (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e, 
                                prod.p_ptech p, prod.p_cable c where e.bp_pttype = 8 and p.pt_id = enreg.pt_id and St_Dwithin(e.geom, St_EndPoint(c.geom),0.0001) 
                                and St_Dwithin(p.geom, St_StartPoint(c.geom),0.0001) AND bp_model IN (1,2,4));

                                counter3 = (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e 
                                where enreg.pt_id = e.bp_pt_code AND bp_model = 5) + (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e, 
                                prod.p_ptech p, prod.p_cable c where e.bp_pttype = 8 and p.pt_id = enreg.pt_id and St_Dwithin(e.geom, St_EndPoint(c.geom),0.0001) 
                                and St_Dwithin(p.geom, St_StartPoint(c.geom),0.0001) AND bp_model = 5);

                                counter4 = (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e 
                                where enreg.pt_id = e.bp_pt_code AND bp_model IN (6,7)) + (select Count(bp_id) from temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ e, 
                                prod.p_ptech p, prod.p_cable c where e.bp_pttype = 8 and p.pt_id = enreg.pt_id and St_Dwithin(e.geom, St_EndPoint(c.geom),0.0001) 
                                and St_Dwithin(p.geom, St_StartPoint(c.geom),0.0001) AND bp_model IN (6,7));

                                IF counter1 > $2 OR counter2 > $3 OR counter3 > $4 OR counter4 > $5 OR (counter1 + counter2 + counter3 + counter4) > 4 then 

                                INSERT INTO temp.erreurs_chambres_""" + zs_refpm.split("_")[2].lower() + """ VALUES (enreg.pt_id, enreg.pt_nature, ARRAY[counter1,counter2,counter3,counter4], enreg.geom);

                                Elsif (counter2 > 0 AND counter1 > 2 * counter2) OR (counter3 > 0 AND counter2 > 2 * counter3) OR (counter4 > 0 AND counter3 > 2 * counter4) then

                                INSERT INTO temp.erreurs_chambres_""" + zs_refpm.split("_")[2].lower() + """ VALUES (enreg.pt_id, enreg.pt_nature, ARRAY[counter1,counter2,counter3,counter4], enreg.geom);

                                Elsif (counter4 >0 AND counter4 = $5 AND (counter1 > 0 OR counter2 > 0 OR counter3 > 0)) OR (counter3 >0 AND counter3 = $4 AND (counter1 > 0 OR counter2 > 0 OR counter4 > 0)) OR (counter2 >0 AND counter2 = $3 AND (counter1 > 0 OR counter3 > 0 OR counter4 > 0)) OR (counter1 >0 AND counter1 = $2 AND (counter2 > 0 OR counter3 > 0 OR counter4 > 0)) then

                                INSERT INTO temp.erreurs_chambres_""" + zs_refpm.split("_")[2].lower() + """ VALUES (enreg.pt_id, enreg.pt_nature, ARRAY[counter1,counter2,counter3,counter4], enreg.geom);

                                End If;

                                End loop;

                                END;
                                $BODY$
                          LANGUAGE plpgsql VOLATILE
                          COST 100;

        """


        try:
            self.executerRequette(define_function, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)


        query = """ DO
                $$
                BEGIN
                DROP TABLE IF EXISTS temp.erreurs_chambres_""" + zs_refpm.split("_")[2].lower() + """;
                CREATE TABLE temp.erreurs_chambres_""" + zs_refpm.split("_")[2].lower() + """ (chambre integer primary key, naturechb varchar, nbebp integer[], geom geometry(Point,2154));
                CREATE INDEX ON public.erreurs_chambres USING GIST(geom);
                perform temp.occupation_chambres('L1T',2,0,0,0,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('A2',3,2,1,0,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('A1',3,2,1,0,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('A3',3,2,1,0,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('L2T',3,2,1,0,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('L2C',3,2,1,0,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('L3T',4,3,1,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('L3C',4,3,1,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('A4',4,4,2,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D1',4,4,2,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D1C',4,4,2,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D1T',4,4,2,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('L4T',4,4,2,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('B1',4,4,3,2,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('L5T',4,4,3,2,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('B2',4,4,4,3,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('L6T',4,4,4,3,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('M1C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('M2T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D2',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D2C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D2T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('M3C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('K1C',4,4,1,0,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('K2C',4,4,2,1,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('K3C',4,4,4,2,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('C1',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D3',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D3C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D3T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P1C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P1T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('C2',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D4',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D4C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('D4T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P2C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('E1',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P3C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('C3',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P4C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P4T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('E2',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('E3',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P5C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P5T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('E4',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P6C',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                perform temp.occupation_chambres('P6T',4,4,4,4,'""" + zs_refpm.split("_")[2] + """');
                END;
                $$ language plpgsql;

        """



        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)

        try:
            self.add_pg_layer("temp", "erreurs_chambres_" + zs_refpm.split("_")[2].lower())
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)



    def update_p_ebp(self):
        ''' Update the table prod.p_ebp with the information from the working table temp.ebp_* '''

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        query = """UPDATE prod.p_ebp as ebp1 SET bp_model = ebp2.bp_model
                FROM temp.ebp_""" + zs_refpm.split("_")[2].lower() + """ as ebp2
                WHERE ebp1.bp_id = ebp2.bp_id;

        """

        try:
            self.executerRequette(query, False)
        except Exception as e:
            self.sendMessageBar(self.critical, "Erreur", str(e), 4)

        self.sendMessageBar(self.info, "Info", "The table prod.p_ebp is updated", 3)