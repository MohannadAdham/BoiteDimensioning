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
        Button_verifier_topologie = self.dlg.findChild(QPushButton, "pushButton_verifier_topologie")
        QObject.connect(Button_verifier_topologie, SIGNAL("clicked()"), self.verify_topology)
        # Connect the button "pushButton_orientation"
        # Button_orientation = self.dlg.findChild(QPushButton, "pushButton_orientation")
        # QObject.connect(Button_orientation, SIGNAL("clicked()"), self.calcul_orientation)

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

                # self.dlg.findChild(QComboBox,"comboBox_suf").setEnabled(True)
                self.dlg.findChild(QComboBox,"comboBox_cheminement").setEnabled(True)
                # self.dlg.findChild(QComboBox,"comboBox_noeud").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_ebp").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_sitetech").setEnabled(True)
                self.dlg.findChild(QComboBox, "comboBox_zs_refpm").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_verifier_topologie").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_orientation").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_fibres_utiles").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_dimensions").setEnabled(True)
                self.dlg.findChild(QPushButton, "pushButton_mettre_a_jour_chemin").setEnabled(True)
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
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_cheminement, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_cheminement')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_ebp, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_ebp')
                self.remplir_menu_deroulant_reference(self.dlg.comboBox_sitetech, ("SELECT tablename as table_lise FROM pg_tables WHERE schemaname = '"+self.dlg.Schema_prod.text()+"' ;"), 'p_sitetech') 
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



    def verify_topology(self):
        # zs_refpm = self.dlg.comboBox_zs_refpm.currentText()
        zs_refpm = self.dlg.comboBox_zs_refpm.currentText()

        self.fenetreMessage(QMessageBox, "Success", "Topology will be verified")
        query_topo = """DO
                    $$
                    DECLARE
                    this_id bigint;
                    this_geom geometry;
                    cluster_id_match integer;

                    id_a bigint;
                    id_b bigint;

                    BEGIN
                    DROP TABLE IF EXISTS prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """;
                    CREATE TABLE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ (cluster_id serial, ids bigint[], geom geometry);
                    CREATE INDEX ON prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ USING GIST(geom);

                    -- Iterate through linestrings, assigning each to a cluster (if there is an intersection)
                    -- or creating a new cluster (if there is not)
                    -- We limit the query to only the concerning ZSRO
                    FOR this_id, this_geom IN (SELECT cm_id, geom FROM prod.p_cheminement WHERE cm_zs_code like '%""" + zs_refpm.split("_")[2] + """%') LOOP
                      -- Look for an intersecting cluster.  (There may be more than one.)
                      SELECT cluster_id FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ WHERE ST_Intersects(this_geom, prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """.geom)
                         LIMIT 1 INTO cluster_id_match;

                      IF cluster_id_match IS NULL THEN
                         -- Create a new cluster
                         INSERT INTO prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ (ids, geom) VALUES (ARRAY[this_id], this_geom);
                      ELSE
                         -- Append line to existing cluster
                         UPDATE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ SET geom = ST_Union(this_geom, geom),
                                              ids = array_prepend(this_id, ids)
                         WHERE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """.cluster_id = cluster_id_match;
                      END IF;
                    END LOOP;

                    -- Iterate through the prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """, combining prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ that intersect each other
                    LOOP
                        SELECT a.cluster_id, b.cluster_id FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ a, prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ b 
                         WHERE ST_Intersects(a.geom, b.geom)
                           AND a.cluster_id < b.cluster_id
                          INTO id_a, id_b;

                        EXIT WHEN id_a IS NULL;
                        -- Merge cluster A into cluster B
                        UPDATE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ a SET geom = ST_Union(a.geom, b.geom), ids = array_cat(a.ids, b.ids)
                          FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ b
                         WHERE a.cluster_id = id_a AND b.cluster_id = id_b;

                        -- Remove cluster B
                        DELETE FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ WHERE cluster_id = id_b;
                    END LOOP;
                    END;
                    $$ language plpgsql;"""

        query_topo_new = """DO
                        $$
                        DECLARE
                        this_id bigint;
                        this_geom geometry;
                        cluster_id_match integer;

                        id_a bigint;
                        id_b bigint;

                        BEGIN
                        DROP TABLE IF EXISTS prod.cm_continuite_""" + zs_refpm.split("_")[2].lower().lower() + """;
                        CREATE TABLE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ (cluster_id serial, ids bigint[], geom geometry);
                        CREATE INDEX ON prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ USING GIST(geom);

                        -- Iterate through linestrings, assigning each to a cluster (if there is an intersection)
                        -- or creating a new cluster (if there is not)
                        -- We limit the query to only the concerning ZSRO
                        FOR this_id, this_geom IN (SELECT cm_id, geom FROM prod.p_cheminement WHERE cm_zs_code like '%""" + zs_refpm.split("_")[2].lower() + """%') LOOP
                          -- Look for an intersecting cluster.  (There may be more than one.)
                          SELECT cluster_id FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ WHERE ST_Intersects(this_geom, prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """.geom)
                             LIMIT 1 INTO cluster_id_match;

                          IF cluster_id_match IS NULL THEN
                             -- Create a new cluster
                             INSERT INTO prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ (ids, geom) VALUES (ARRAY[this_id], this_geom);
                          ELSE
                             -- Append line to existing cluster
                             UPDATE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ SET geom = ST_Union(this_geom, geom),
                                                  ids = array_prepend(this_id, ids)
                             WHERE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """.cluster_id = cluster_id_match;
                          END IF;
                        END LOOP;

                        -- Iterate through the prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """, combining prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ that intersect each other
                        LOOP
                            SELECT a.cluster_id, b.cluster_id FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ a, prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ b 
                             WHERE ST_Intersects(a.geom, b.geom)
                               AND a.cluster_id < b.cluster_id
                              INTO id_a, id_b;

                            EXIT WHEN id_a IS NULL;
                            -- Merge cluster A into cluster B
                            UPDATE prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ a SET geom = ST_Union(a.geom, b.geom), ids = array_cat(a.ids, b.ids)
                              FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ b
                             WHERE a.cluster_id = id_a AND b.cluster_id = id_b;

                            -- Remove cluster B
                            DELETE FROM prod.cm_continuite_""" + zs_refpm.split("_")[2].lower() + """ WHERE cluster_id = id_b;
                        END LOOP;
                        END;
                        $$ language plpgsql;"""


        self.fenetreMessage(QMessageBox, "info", query_topo)
        self.executerRequette(query_topo, False)
        self.fenetreMessage(QMessageBox, "Success", "Topology has been verified")
        try:
            self.add_pg_layer("prod", "cm_continuite_" + zs_refpm.split("_")[2].lower())
        except Exception as e:
            self.fenetreMessage(QMessageBox.Warning,"Erreur_fenetreMessage", str(e))
            # self.fenetreMessage(QMessageBox, "Success", "The topology verification layer wasn't added to the map")
        # self.fenetreMessage(QMessageBox, "Success", "The topology verification layer is added to the map")




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






