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
        # Button_verifier_orientation = self.dlg.findChild(QPushButton, "pushButton_verifier_orientation")  
        # QObject.connect(Button_orientation, SIGNAL("clicked()"), self.verifier_orientation)

        # Connect the button "pushButton_fibres_utiles"
        # Button_fibres_utiles = self.dlg.findChild(QPushButton, "pushButton_fibres_utiles")
        # QObject.connect(Button_fibres_utiles, SIGNAL("clicked()"), self.calcul_fibres_utiles)

        # Connect the button "pushButton_"
        # Button_dimensios = self.dlg.findChild(QPushButton, "pushButton_dimensions")
        # QObject.connect(Button_dimensios, SIGNAL("clicked()"), self.calcul_cable_dimensions)

        # Connect the butoon "pushButton_mettre_a_jour_chemin"
        # Button_mettre_a_jour_chemin = self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_chemin")
        # QObject.connect(Button_mettre_a_jour_chemin, SIGNAL("clicked()"), self.update_p_cheminement)

        # Connect the button "pushButton_mettre_a_jour_cable"
        # Button_mettre_a_jour_cable = self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_cable")
        # QObject.connect(Button_mettre_a_jour_cable, SIGNAL("clicked()"), self.update_p_cable)





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
        try:
            msg = QMessageBox()
            # msg.setIcon(typeMessage)
            msg.setWindowTitle(titre)
            msg.setText(str(message))
            msg.setWindowFlags(PyQt4.QtCore.Qt.WindowStaysOnTopHint)
            msg.exec_()
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage",str(e))



    def GetParamBD(self, dbname, password, user, serveur, sche):
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
            self.fenetreMessage(QMessageBox.Warning,"Erreur_GetParamBD",str(e))
            # print str(e)


    def remplir_menu_deroulant_reference(self, combobox, rq_sql, DefValChamp):
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
                self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_cable").setEnabled(True)

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
                # self.dlg2.findChild(QPushButton,"pushButton_controle_avt_migration").setEnabled(True)
            else:
                # self.dlg2.findChild(QPushButton,"pushButton_controle_avt_migration").setEnabled(False)
                # self.dlg2.findChild(QPushButton,"pushButton_migration").setEnabled(False)
                print "Schema not found"
        except Exception as e:
                pass



    def verify(self):
        # zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        self.fenetreMessage(QMessageBox, "Success", "verifications will be performed")

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


        self.fenetreMessage(QMessageBox, "info", "verification will be executed")

        try:
            self.executerRequette(query_verify, False)
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))



        self.fenetreMessage(QMessageBox, "Success", "verification is done!")

        # try:
        #     self.add_pg_layer("prod", "cm_continuite_" + zs_refpm.split("_")[2].lower())
        # except Exception as e:
        #     self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))


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
                self.fenetreMessage(QMessageBox.Warning,"Warning", "Consultz la table : " + table_name + '_' + zs_refpm.split("_")[2].lower())





    def add_style(self, layer):
        from random import randrange
        # self.fenetreMessage(QMessageBox, 'info', 'within add style for layer ' + layer.name())

        # Get the active layer (must be a vector layer)
        # layer = qgis.utils.iface.activeLayer()

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

            if layer.wkbType()==QGis.WKBPoint:
                # print 'Layer is a pojnt layer'
                layer_style['color'] = '%d, %d, %d' % (randrange(0,256), randrange(0,256), randrange(0,256))
                layer_style['size'] = '2'
                symbol_layer = QgsSimpleMarkerSymbolLayerV2.create(layer_style)
                symbol_layer.setOutlineWidth(0)


            if layer.wkbType()==QGis.WKBLineString:
                # print 'Layer is a line layer'
                layer_style['width_border'] = '0.46'
                layer_style['size'] = '0.46'
                # layer_style['color_border'] = 'red'
                symbol_layer = QgsSimpleFillSymbolLayerV2.create(layer_style)


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
        # Create a data source URI
        uri = QgsDataSourceURI()

        # set host name, port, database name, username and password
        uri.setConnection(self.dlg.lineEdit_Host.text(), "5432", self.dlg.lineEdit_BD.text(), self.dlg.lineEdit_User.text(), self.dlg.lineEdit_Password.text())

        # set database schema, table name, geometry column and optionally subset (WHERE clause)
        # uri.setDataSource('temp', 'cheminement_al01', "geom")
        uri.setDataSource(schema, table_name, "geom")

        vlayer = QgsVectorLayer(uri.uri(False), table_name, "postgres")

        # if not vlayer.isValid():
        #     self.fenetreMessage(QMessageBox, "Error", "The layer %s is not valid" % vlayer.name())
        #     return


        # check first if the layer is already added to the map
        layer_names = [layer.name() for layer in QgsMapLayerRegistry.instance().mapLayers().values()]
        if table_name not in layer_names:
            # Add the vector layer to the map
            QgsMapLayerRegistry.instance().addMapLayers([vlayer])
            self.fenetreMessage(QMessageBox, "Success", "Layer %s is loaded" % vlayer.name())

        else :
            self.fenetreMessage(QMessageBox, "Success", "Layer %s already exists but it has been updated" % vlayer.name())



    def create_temp_cable_table(self, zs_refpm):
        self.fenetreMessage(QMessageBox, "info", "within create_temp_cable_table")

        query = """ DROP TABLE IF EXISTS temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """;
                CREATE TABLE temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """ 
                as (SELECT cable.* FROM prod.p_cable as cable JOIN prod.p_ltech ON cb_lt_code = lt_id JOIN prod.p_zsro ON lt_id = zs_lt_code WHERE zs_refpm = '""" + zs_refpm + """');

        """

        try:
            self.executerRequette(query, False)

        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning, "Erreur_fenetreMessage", str(e))





    def calcul_orientation_cable(self):

        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        self.fenetreMessage(QMessageBox, "info", "before create_temp_cable_table")
        

        self.create_temp_cable_table(zs_refpm)

        # self.create_cable_cluster(zs_refpm)



        query_orientation = """

        """

        # try:
        #     self.executerRequette(query_orientation, False)
        # except Exception as e:
        #     self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))



    def create_cable_cluster(self, zs_refpm):

        self.fenetreMessage(QMessageBox, "info", "within create_cable_cluster")

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
                            
                            FOR nro IN (SELECT c.cb_id, c.cb_code,c.cb_lt_code, c.geom, s.st_nom FROM temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """ c, prod.p_sitetech s 
                            WHERE ST_INTERSECTS(c.geom, s.geom) AND st_id = 2 AND c.cb_lt_code = 4 ) 
                            LOOP -- Vérifier site technique
                            
                            INSERT INTO temp.cb_cluster_""" + zs_refpm.split("_")[2] + """(this_id, cb_code, cb_lt_code, cb_r3_code, rang, hierarchie, geom)   
                            SELECT nro.cb_id, nro.cb_code, nro.cb_lt_code, nro.st_nom, counter, CONCAT(counter, '.',counter2), nro.geom;

                            counter2 = counter2 + 1;

                            END LOOP;

                            FOR id IN (SELECT cb_id FROM temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """ WHERE cb_code <> 26)

                            LOOP
                            
                            counter = counter + 1;
                            
                            INSERT INTO temp.cb_cluster_""" + zs_refpm.split("_")[2] + """(this_id, cb_code, cb_lt_code, cb_r3_code, rang, hierarchie, passage, geom)
                            SELECT c.cb_id, c.cb_code, l. cb_lt_code, l. cb_r3_code, counter, CONCAT(counter,'.',
                            ROW_NUMBER() OVER(PARTITION BY l.hierarchie ORDER BY ST_X(ST_EndPoint(ST_INTERSECTION(ST_BUFFER(ST_STARTPOINT(c.geom), 1), c.geom)))),'.', l.hierarchie) as hierarchie, 
                                CASE WHEN ST_Touches(c.geom, St_EndPoint(l.geom)) AND c.cb_code = l.cb_code AND l.passage IS NULL THEN l.this_id 
                                     WHEN ST_Touches(c.geom, St_EndPoint(l.geom)) AND c.cb_code = l.cb_code AND l.passage IS NOT NULL THEN l.passage END as test, c.geom
                            FROM temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """ c, temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ l
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
                                    LEFT JOIN (SELECT SUBSTRING(b.ba_etiquet, 11,4)::varchar as quadri, c4.hierarchie FROM temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """ ca , temp.cb_cluster_""" + zs_refpm.split("_")[2] + """ c4, prod.p_baie b WHERE b.ba_id = ca.cb_ba1 AND c4.this_id = ca.cb_id AND ca.cb_ba1 IS NOT NULL) c3 ON c3.hierarchie = RIGHT(c1.hierarchie, 3)
                                    ORDER BY RIGHT(c2.hierarchie, 3),  c2.rang, LEFT(c2.hierarchie, 50), RIGHT(c1.hierarchie, 3),  c1.rang, LEFT(c1.hierarchie, 50) 
                                    ) AS A
                                ) AS B
                            WHERE temp.cb_cluster_""" + zs_refpm.split("_")[2] + """.this_id = B.this_id;


                            UPDATE temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """
                            SET cb_etiquet = B.etiquette,
                                cb_lt_code = B.cb_lt_code,
                                cb_r3_code = B.cb_r3_code
                            FROM (
                                SELECT * 
                                FROM temp.cb_cluster_""" + zs_refpm.split("_")[2] + """
                                 ) as B
                            WHERE temp.cable_for_boite_""" + zs_refpm.split("_")[2] + """.cb_id = b.this_id;*/
                            
                        END;
                        $$ language plpgsql;
        

        """


        # try:
        #     self.executerRequette(query_cluster, False)
        #     self.fenetreMessage(QMessageBox, "info", "The table cb_cluster is created")


        # except Exception as e:
        #     self.fenetreMessage(QMessageBox.Warning, "Erreur_fenetreMessage", str(e))




    def verify_orientation_cable(self):
        pass


    def calcul_fibres_utiles(self):
        pass








