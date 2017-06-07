# login.py
# -*- coding: utf-8 -*-

# Copyright (c) 2010 Fondazione Ugo Bordoni.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import Tkinter
import hashlib
import logging
import os
import sys
import tkMessageBox

from getconf import getconf
import myProp
import paths
from common import utils

logger = logging.getLogger(__name__)

_clientConfigurationFile = 'client.conf'
_configurationServer = 'https://finaluser.agcom244.fub.it/Config'


class LoginException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class LoginAuthenticationException(LoginException):
    def __init__(self, message):
        Exception.__init__(self, message)


class LoginConnectionException(LoginException):
    def __init__(self, message):
        Exception.__init__(self, message)


class LoginCancelledException(LoginException):
    def __init__(self, message=""):
        Exception.__init__(self, message)


### Activation code ###
def getCode():
    '''
    Apre una finestra che chiede il codice licenza. Resituisce il codice licenza e chiude la finestra.
    '''
    root = Tkinter.Tk()
    if utils.is_windows():
        root.wm_iconbitmap('../Nemesys.ico')
    app = LoginGui(master=root)
    app.master.title("Attivazione Ne.Me.Sys")
    app.mainloop()
    appresult = str(app.result)
    logger.info(appresult)

    if appresult == 'Cancel':
        logger.info("User pressed Cancel button, exiting")
        raise LoginCancelledException()

    if appresult == '' or len(appresult) < 4:
        appresult = None
        logger.error('Exit: wrong activation code')
        CodeError()
        raise LoginAuthenticationException('Wrong username/password')

    if root:
        root.destroy()
    return appresult


def CodeError():
    """
    Errore in caso di credenziali errate
    """
    message = '''Autenticazione fallita o licenza non attiva.
                Controllare i dati di accesso e la presenza di una licenza attiva al sito www.misurainternet.it'''
    ErrorDialog(message)


def ConnectionError():
    """
    Errore in caso di connessione fallita
    """
    message = '''Connessione fallita.
    Controllare di avere accesso alla rete.'''
    ErrorDialog(message)


def FinalError():
    """
    Errore in caso di tentativo di download non andato a buon fine
    """
    message = '''Si è verificato un errore. Controllare:

    - di avere accesso alla rete,
    - di aver digitato correttamente le credenziali di accesso,
    - di avere una licenza attiva,
    - di non aver ottenuto un certificato con Ne.Me.Sys. meno di 45 giorni antecedenti ad oggi.

    Dopo 5 tentativi di accesso falliti, sarà necessario disinstallare Ne.Me.Sys e reinstallarlo nuovamente.'''
    ErrorDialog(message)


def MaxError():
    """
    Errore in caso di quinto inserimento errato di credenziali
    """
    message = '''Le credenziali non sono corrette o la licenza non è più valida.
              Procedere con la disinstallazione e reinstallare nuovamente Ne.Me.Sys. \
              dopo aver controllato user-id e password che ti sono state invitate in fase \
              di registrazione o a richiedere una nuova licenza dalla tua area privata sul sito misurainternet.it.'''
    ErrorDialog(message)


def CancelError():
    """
    Utente e' uscito
    """
    message = '''L'autenticazione non e' andata a buon fine.
               Procedere con la disinstallazione e reinstallare nuovamente Ne.Me.Sys. \
               dopo aver controllato user-id e password che ti sono state invitate in fase \
               di registrazione o a richiedere una nuova licenza dalla tua area privata sul sito misurainternet.it.'''
    ErrorDialog(message)
    sys.exit()


def ErrorDialog(message):
    root = Tkinter.Tk()
    if utils.is_windows():
        root.wm_iconbitmap('../Nemesys.ico')
    root.withdraw()
    title = 'Errore'
    tkMessageBox.showerror(title, message, parent=root)
    root.destroy()


def OkDialog():
    root = Tkinter.Tk()
    if utils.is_windows():
        root.wm_iconbitmap('../Nemesys.ico')
    root.withdraw()
    title = 'Ne.Me.Sys autenticazione corretta'
    message = 'Username e password corrette e verificate'
    tkMessageBox.showinfo(title, message, parent=root)
    root.destroy()


### Function to Download Configuration File ###
def getActivationFile(appresult, path, config_path):
    '''
      Scarica il file di configurazione. Ritorna True se tutto è andato bene
    '''
    logger.info('getActivationFile function')

    ac = appresult
    logger.info('Codici ricevuti: %s' % ac)

    download = False
    try:
        download = getconf(ac, path, _clientConfigurationFile, _configurationServer)
        logger.info('download = %s' % str(download))
    except Exception as e:
        logger.error('Cannot download the configuration file: %s' % str(e))
        raise LoginConnectionException(str(e))
    if download is not True:
        logger.info('Received error from server, wrong credentials or license not active')
        raise LoginAuthenticationException("")
    else:
        logger.info('Configuration file successfully downloaded')
        myProp.writeProps(config_path, '\nregistered', 'ok')
        OkDialog()
        return True


class LoginGui(Tkinter.Frame):
    """
    finestra di codice licenza
    """

    def sendMsg(self):
        inserted_username = self.username.get()
        inserted_password = self.password.get()
        if (inserted_username and inserted_password):
            self.result = "%s|%s" % (self.username.get(), hashlib.sha1(self.password.get()).hexdigest())
        self.quit()

    def cancel(self):
        self.result = 'Cancel'
        self.quit()

    def createWidgets(self):
        self.Title = Tkinter.Label(self, padx=60, pady=8)
        self.Title["text"] = '''Inserisci i codici di accesso (username e password)
        che hai usato per accedere all'area personale'''
        self.Title.grid(column=0, row=0, columnspan=2)

        username_label = Tkinter.Label(self, text="username:")
        username_label.grid(column=0, row=1)

        self.username = Tkinter.Entry(self, width=30)
        self.username.grid(column=1, row=1)

        password_label = Tkinter.Label(self, text="password:")
        password_label.grid(column=0, row=2)

        self.password = Tkinter.Entry(self, width=30)
        self.password["show"] = "*"
        self.password.grid(column=1, row=2)

        self.button_frame = Tkinter.Frame(self)
        self.button_frame.grid(column=1, row=3, columnspan=2, pady=8)

        self.invio = Tkinter.Button(self.button_frame)
        self.invio["text"] = "Accedi",
        self.invio["command"] = self.sendMsg
        self.invio.grid(column=0, row=0, padx=4)

        self.cancl = Tkinter.Button(self.button_frame)
        self.cancl["text"] = "Cancel",
        self.cancl["command"] = self.cancel
        self.cancl.grid(column=1, row=0, padx=4)

    def __init__(self, master=None):
        Tkinter.Frame.__init__(self, master)
        self.config(width="800")
        if utils.is_windows():
            self.master.wm_iconbitmap(os.path.join('..', 'nemesys.ico'))
        self.pack()
        self.createWidgets()
        self.result = None


def main():
    ###  DISCOVERING PATH  ###
    try:
        _PATH = os.path.dirname(sys.argv[0])
        if _PATH == '':
            _PATH = "." + os.sep
        if _PATH[len(_PATH) - 1] != os.sep:
            _PATH = _PATH + os.sep
    except Exception as e:
        _PATH = "." + os.sep

    config_path = _PATH + "cfg" + os.sep + "cfg.properties"

    ###  READING PROPERTIES  ###
    _prop = None
    try:
        _prop = myProp.readProps(config_path)
    except Exception as e:
        logger.error("Could not read configuration file from %s" % config_path)
        ErrorDialog("File di configurazione non trovata in %s, impossibile procedere con l'installazione" % config_path)
        sys.exit(1)

    if 'code' not in _prop:
        result = False
        j = 0
        has_canceled = False
        # Al massimo faccio fare 5 tentativi di inserimento codice di licenza
        while not result and j < 5 and not has_canceled:
            # Prendo un codice licenza valido sintatticamente
            appresult = None
            errorfunc = None
            try:
                appresult = getCode()
                result = getActivationFile(appresult, paths._CONF_DIR, config_path)
            except LoginAuthenticationException as e:
                logger.warning("Authentication failure n. %d" % j)
                errorfunc = CodeError
            except LoginConnectionException as e:
                logger.warning("Authentication connection problem: %s" % str(e))
                errorfunc = ConnectionError
            except LoginCancelledException:
                has_canceled = True
            except Exception as e:
                logger.error("Caught exception while downloading configuration file: %s" % str(e))

            if result is False and not has_canceled and j < 4:
                if errorfunc:
                    errorfunc()
                else:
                    logger.warning('Final Error occurred at attempt number %d' % j)
                    FinalError()
            j += 1

        if has_canceled:
            CancelError()
            sys.exit(0)
        elif result is False:
            MaxError()
            logger.warning('MaxError occurred at attempt number 5')
            myProp.writeProps(config_path, '\ncode', appresult)
            _prop = myProp.readProps(config_path)
            myProp.writeProps(config_path, '\nregistered', 'nok')
            _prop = myProp.readProps(config_path)
            sys.exit(1)
        elif result is True:
            logger.info('License file successfully downloaded')
            myProp.writeProps(config_path, '\ncode', appresult)
            _prop = myProp.readProps(config_path)
    else:
        logger.debug('Activation Code found')
        if 'registered' in _prop:
            # Ho tentato almeno una volta il download
            logger.debug('Registered in _prop')
            status = str(_prop['registered'])
            if status == 'ok':
                # Allora posso continuare lo start del servizio
                logger.debug('Status of registered is Ok')
                logger.info('Configuration file already downloaded')
            else:
                # Il servizio non può partire
                logger.error('Login previously failed. ')
                # Dialog to unistall and retry
                MaxError()


if __name__ == '__main__':
    import log_conf

    log_conf.init_log()
    main()
