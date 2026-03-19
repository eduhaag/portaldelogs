/************************************************************************************************
** Procedures para limpeza de logs do Progress/Appserver/WebSpeed
************************************************************************************************/

PROCEDURE logClear:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cClean   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cExt     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTamFile AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTmp     AS CHARACTER NO-UNDO.

    ASSIGN cClean = SUBSTR(pArq, 1, R-INDEX(pArq, ".") - 1)
           cExt   = SUBSTR(pArq, R-INDEX(pArq, ".") + 1, LENGTH(pArq)).

    DEFINE VARIABLE lTraducao AS LOGICAL NO-UNDO LABEL "Traducao/Facelift"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lRpw      AS LOGICAL NO-UNDO LABEL "RPW"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProConn  AS LOGICAL NO-UNDO LABEL "DB.Connects"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProEvent AS LOGICAL NO-UNDO LABEL "PROEVENTS"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProDyn   AS LOGICAL NO-UNDO LABEL "DYNOBJECTS"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProTrans AS LOGICAL NO-UNDO LABEL "4GLTRANS"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProMsg   AS LOGICAL NO-UNDO LABEL "4GLMESSAGES"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProTrace AS LOGICAL NO-UNDO LABEL "4GLTRACE"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProFile  AS LOGICAL NO-UNDO LABEL "FILEID"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProQuery AS LOGICAL NO-UNDO LABEL "QRYINFO"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lDI       AS LOGICAL NO-UNDO LABEL "DI"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lLS       AS LOGICAL NO-UNDO LABEL "License Server"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lDDK      AS LOGICAL NO-UNDO LABEL "Templates DDK"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lDBO      AS LOGICAL NO-UNDO LABEL "BOs"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lFluig    AS LOGICAL NO-UNDO LABEL "Fluig"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lEAI      AS LOGICAL NO-UNDO LABEL "EAI"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE lProcesso AS LOGICAL NO-UNDO LABEL "Quebra por Processo"
                                VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE cTrgFile  AS CHARACTER NO-UNDO LABEL "Pasta Destino" FORMAT "x(255)"
                                VIEW-AS EDITOR SIZE 100 BY 1.

    DEFINE BUTTON btConv LABEL "Processa Arquivo".
    
    DEFINE RECTANGLE rtQuebra   SIZE 170 BY 2 BGCOLOR 8.
    DEFINE RECTANGLE rtDtsul    SIZE 170 BY 4 BGCOLOR 8.
    DEFINE RECTANGLE rtProg     SIZE 170 BY 4 BGCOLOR 8.
     
    DEFINE FRAME f-log
        cTrgFile  AT ROW 01.5 COL 3 SPACE(0) btArq SPACE(5) btConv btExit
        
        rtQuebra  AT ROW 03.0 COL 3 
        "Quebras" AT ROW 02.5 COL 5        
        lProcesso AT ROW 03.5 COL 5

        rtDtsul   AT ROW 06.0 COL 3 
        "Totvs Eliminar" AT ROW 05.5 COL 5        
        lTraducao AT ROW 06.5 COL 5 
        lRpw      AT ROW 06.5 COL 40
        lDI       AT ROW 06.5 COL 70 
        lLS       AT ROW 07.5 COL 5
        lDDK      AT ROW 07.5 COL 40
        lDBO      AT ROW 07.5 COL 70 
        lFluig    AT ROW 08.5 COL 5 
        lEAI      AT ROW 08.5 COL 40
        
        rtProg    AT ROW 11.0 COL 3 
        "Progress Eliminar" AT ROW 10.5 COL 5        
        lProConn  AT ROW 11.5 COL 5
        lProEvent AT ROW 11.5 COL 40
        lProDyn   AT ROW 11.5 COL 70
        lProTrans AT ROW 12.5 COL 5
        lProFile  AT ROW 12.5 COL 40
        lProMsg   AT ROW 12.5 COL 70
        lProTrace AT ROW 13.5 COL 5
        lProQuery AT ROW 13.5 COL 40
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28 BGCOLOR 8.

/*        
        4GLMessages,
        4GLTrace,
        DB.Connects,
        DynObjects.DB,DynObjects.XML,DynObjects.Other,DynObjects.CLASS,DynObjects.UI,
        FileID,
        ProEvents.UI.CHAR,ProEvents.UI.COMMAND,ProEvents.Other,
        SAX
*/

    ON  CHOOSE OF btConv DO:
        ASSIGN cTrgFile     lProcesso
               lTraducao    lRpw
               lDI          lLS
               lDDK         lProConn
               lProEvent    lProDyn
               lProTrans    lProFile
               lDBO         lProMsg
               lFluig       lEAI
               lProTrace    lProQuery.

        PUBLISH "setPropParam"    FROM THIS-PROCEDURE ("clear_dirDestino", cTrgFile).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_QuebraPorProcesso", lProcesso).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiTraducao", lTraducao).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiRpw", lRPW).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiDI", lDI).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiLS", lLS).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiDDK", lDDK).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiDBO", lDBO).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiFluig", lFluig).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiEAI", lEAI).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProConn", lProConn).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProEvent", lproEvent).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProDyn", lproDyn).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProTrans", lproTrans).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProFile", lProFile).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProMessages", lProMsg).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProTrace", lProTrace).
        PUBLISH "setPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProQuery", lProQuery).

        PUBLISH "saveProp" FROM THIS-PROCEDURE.
        
        SESSION:SET-WAIT-STATE("general").
        RUN importaClear (pDir, pArq, cTrgFile, lProcesso,
                          lTraducao, lRpw, lDI, lLS, lDDK, lDBO, lFluig, lEAI,
                          lProConn, lProEvent, lProDyn, lProTrans, lProFile, lProMsg, 
                          lProTrace, lProQuery).
        
        SESSION:SET-WAIT-STATE("").
        HIDE MESSAGE NO-PAUSE.
    END.

    ON  CHOOSE OF btArq DO:
        ASSIGN cTrgFile.
        ASSIGN cTrgFile = REPLACE(cTrgFile, "/", "~\").
        
        DEFINE VARIABLE lResp AS LOG NO-UNDO.
        SYSTEM-DIALOG GET-DIR cTrgFile
            TITLE "Selecione o diretorio para destino dos logs processados"
            INITIAL-DIR cTrgFile
            RETURN-TO-START-DIR
            UPDATE lResp.

        ASSIGN cTrgFile = REPLACE(cTrgFile, "~\", "/") + "/".
        DISPLAY cTrgFile WITH FRAME f-log.
    END.
    
    ASSIGN lTraducao = TRUE
           lLS       = TRUE
           lEAI      = TRUE
           lFluig    = TRUE
           lDDK      = TRUE
           lDBO      = TRUE
           lProConn  = TRUE
           lProEvent = TRUE
           lProDyn   = TRUE
           lProTrans = TRUE
           lProTrace = FALSE
           lProQuery = TRUE.
    
    PUBLISH "getPropParam"    FROM THIS-PROCEDURE ("clear_dirDestino", OUTPUT cTrgFile).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_QuebraPorProcesso", OUTPUT lProcesso).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiTraducao", OUTPUT lTraducao).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiRpw", OUTPUT lRPW).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiDI", OUTPUT lDI).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiLS", OUTPUT lLS).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiDDK", OUTPUT lDDK).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiDBO", OUTPUT lDBO).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiFluig", OUTPUT lFluig).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiEAI", OUTPUT lEAI).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProConn", OUTPUT lProConn).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProEvent", OUTPUT lproEvent).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProDyn", OUTPUT lproDyn).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProTrans", OUTPUT lproTrans).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProFile", OUTPUT lProFile).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProMessages", OUTPUT lProMsg).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProTrace", OUTPUT lProTrace).
    PUBLISH "getPropParamLog" FROM THIS-PROCEDURE ("clear_ExcluiProQuery", OUTPUT lProQuery).
    
    ASSIGN hFrame   = FRAME f-log:Handle.
    
    ASSIGN cTrgFile = pDir.

    ENABLE ALL WITH FRAME f-log.
    
    DISPLAY cTrgFile     lProcesso
            lTraducao    lRpw
            lDI          lLS
            lDDK         lProConn
            lProEvent    lProDyn
            lProTrans    lProFile
            lDBO         lProMsg
            lFluig       lEAI
            lProTrace    lProQuery
            WITH FRAME f-log.

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-log.
    END.

    FINALLY:
        HIDE MESSAGE NO-PAUSE.
        HIDE FRAME f-log NO-PAUSE.
    END.
END PROCEDURE.

PROCEDURE importaClear:
    DEFINE INPUT PARAMETER cDir      AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cArq      AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cTrgFile  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER lProcesso AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lTraducao AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lRpw      AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lDI       AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lLS       AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lDDK      AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lDBO      AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lFluig    AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lEAI      AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProConn  AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProEvent AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProDyn   AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProTrans AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProFile  AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProMsg   AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProTrace AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lProQuery AS LOGICAL   NO-UNDO.
    
    DEFINE VARIABLE cArq2     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iLinOrg   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iFileLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iProcLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cProc     AS CHARACTER NO-UNDO.

    ASSIGN FILE-INFO:FILENAME = cDir + cArq
           iFileLen           = FILE-INFO:FILE-SIZE
           cInfo              = "".

    IF  lProcesso = FALSE THEN DO: 
        ASSIGN cArq2 = ENTRY(1,cArq,".") + "_clean." + ENTRY(NUM-ENTRIES(cArq, "."),cArq,".").
        OUTPUT stream sDad TO value(cTrgFile + "/" + cArq2).
    END.

    INPUT stream sImp FROM value(cDir + "/" + cArq).
    REPEAT :
        ASSIGN iLinOrg = iLinOrg + 1.
        IMPORT STREAM sImp UNFORMATTED cLin.
        ASSIGN iProcLen = iProcLen + length(cLin).

        IF  TRIM(cLin) = "" THEN
            NEXT.

        ASSIGN cLin = TRIM(cLin).

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Processando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.
        
        IF  substr(cLin, 1, 1) <> "[" 
        OR  LENGTH(cLin) < 60 THEN
            NEXT.

        /* traducao e facelift */
        IF  lTraducao = TRUE THEN DO:
            IF  INDEX(cLin, "utp/ut-liter.p")     > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-trfrrp.p")    > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-trdfr.p")     > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-trdfr.p")     > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-fiel2.p")     > 0 THEN NEXT.
            IF  INDEX(cLin, "btb/btb901zo.p")     > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-fill-in")    > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-toggle-box") > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-text")       > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-radio-set")  > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-button")     > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-editor")     > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-browse")     > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-menu")       > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trad-combo-box")  > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-field.p")     > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-trcampos.p")  > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_aplica_facelift") > 0 THEN NEXT.
            IF  INDEX(cLin, "btb908za") > 0 THEN DO:
                IF  INDEX(cLin, "Func fn_trad")   > 0 THEN NEXT.
            END.
        END.

        /* rpw */
        IF  lRpw = TRUE THEN DO:
            IF  INDEX(cLin, "pi_verificar_ped_exec_a_executar")   > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_verificar_ped_exec_pendurados")   > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_servid_exec_status")              > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_sec_to_formatted_time")           > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_formatted_time_to_sec")           > 0 THEN NEXT.            
            IF  INDEX(cLin, "pi_atualiza_tt_ped_exec")            > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_open_servid_exec")                > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_vld_servid_exec_autom")           > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_disparar_ped_exec_ems2")          > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_montar_lista_servid_exec_dispon") > 0 THEN NEXT.
            IF  INDEX(cLin, "pi_vld_fnc_servid_exec")             > 0 THEN NEXT.
            IF  INDEX(cLin, "btb908za") > 0 THEN DO:
                IF  INDEX(cLin, "fn_situacao ")           > 0 THEN NEXT.
                IF  INDEX(cLin, "fn_motivo ")             > 0 THEN NEXT.
                IF  INDEX(cLin, "fn_trad ")               > 0 THEN NEXT.
                IF  INDEX(cLin, "pi-inicializa-variavel") > 0 THEN NEXT.
            END.
        END.

        /* DI */
        IF  lDI = TRUE THEN DO:
            IF  INDEX(cLin, "piSetUserDB ")        > 0 THEN NEXT.
            IF  INDEX(cLin, "piConectar ")         > 0 THEN NEXT.
            IF  INDEX(cLin, "4GLSession ")         > 0 THEN NEXT.
            IF  INDEX(cLin, "CtrlFrame.PSTimer")   > 0 THEN NEXT.
            IF  INDEX(cLin, "men/men702dd.p")      > 0 THEN NEXT.
            IF  INDEX(cLin, "men/men702dc.w")      > 0 THEN NEXT.
            IF  INDEX(cLin, "men/men906zb.p")      > 0 THEN NEXT.
            IF  INDEX(cLin, "men/men906zatimeout") > 0 THEN NEXT.
            IF  INDEX(cLin, "fwk/utils/diProgress.p") > 0 THEN DO:
                IF  INDEX(cLin, "piEncerrarDI")               > 0 THEN NEXT.
                IF  INDEX(cLin, "piEncerrarDISemPSTimer")     > 0 THEN NEXT.
                IF  INDEX(cLin, "piTTDialog")                 > 0 THEN NEXT.
                IF  INDEX(cLin, "piEliminarDialog")           > 0 THEN NEXT.
                IF  INDEX(cLin, "piAcelerarIntervaloPSTimer") > 0 THEN NEXT.
                IF  INDEX(cLin, "piEncerrarProcesso")         > 0 THEN NEXT.
                IF  INDEX(cLin, "disable_UI")                 > 0 THEN NEXT.
                IF  INDEX(cLin, "socketConnected")            > 0 THEN NEXT.
                IF  INDEX(cLin, "AliveNKickn")                > 0 THEN NEXT.
                IF  INDEX(cLin, "doLog")                      > 0 THEN NEXT.
                IF  INDEX(cLin, "TimerRegistrado")            > 0 THEN NEXT.
                IF  INDEX(cLin, "ExtendedModeLog")            > 0 THEN NEXT.
                IF  INDEX(cLin, "loadTimer")                  > 0 THEN NEXT.
                IF  INDEX(cLin, "TimerActive")                > 0 THEN NEXT.
                IF  INDEX(cLin, "RegOpenKeyA")                > 0 THEN NEXT.
                IF  INDEX(cLin, "RegCloseKey")                > 0 THEN NEXT.
                IF  INDEX(cLin, "RegEnumKeyA")                > 0 THEN NEXT.
                IF  INDEX(cLin, "RegQueryValueExA")           > 0 THEN NEXT.
                IF  INDEX(cLin, "RegSetValueExA")             > 0 THEN NEXT.
                IF  INDEX(cLin, "piApplyEndErrorDialog")      > 0 THEN NEXT.
                IF  INDEX(cLin, "piApplyWindowCloseDialog")   > 0 THEN NEXT.
                IF  INDEX(cLin, "piFecharJanela")             > 0 THEN NEXT.
                IF  INDEX(cLin, "piEliminarObjeto")           > 0 THEN NEXT.
                IF  INDEX(cLin, "piEliminarClasses")          > 0 THEN NEXT.
                IF  INDEX(cLin, "piDesconectarBancos")        > 0 THEN NEXT.
                IF  INDEX(cLin, "piFecharProgramaGUI")        > 0 THEN NEXT.
                IF  INDEX(cLin, "enable_UI")                  > 0 THEN NEXT.
                IF  INDEX(cLin, "executeProgram")             > 0 THEN NEXT.
                IF  INDEX(cLin, "instLicManager")             > 0 THEN NEXT.
                IF  INDEX(cLin, "licManagerLoc")              > 0 THEN NEXT.
                IF  INDEX(cLin, "verifyLicense")              > 0 THEN NEXT.
                IF  INDEX(cLin, "sendProcedure")              > 0 THEN NEXT.
                IF  INDEX(cLin, "readProcedure")              > 0 THEN NEXT.
                IF  INDEX(cLin, "receivedProcedure")          > 0 THEN NEXT.
                IF  INDEX(cLin, "piGetIdle")                  > 0 THEN NEXT.
                IF  INDEX(cLin, "piUpdateInfo")               > 0 THEN NEXT.
                IF  INDEX(cLin, "piValidNegocio")             > 0 THEN NEXT.
                IF  INDEX(cLin, "piSetInfoUserCompany")       > 0 THEN NEXT.
                IF  INDEX(cLin, "piUpdateProperties")         > 0 THEN NEXT.
                IF  INDEX(cLin, "piUpdateInfoLS")             > 0 THEN NEXT.
                IF  INDEX(cLin, "piUpdateInfoServer")         > 0 THEN NEXT.
                IF  INDEX(cLin, "piUpdateInfoLogin")          > 0 THEN NEXT.
                IF  INDEX(cLin, "piUpdateInfoAppServer")      > 0 THEN NEXT.
                IF  INDEX(cLin, "piAtualizTitEmpresa")        > 0 THEN NEXT.
                IF  INDEX(cLin, "piAtualizaMessage")          > 0 THEN NEXT.
                IF  INDEX(cLin, "piAtualizaEmpresa")          > 0 THEN NEXT.
                IF  INDEX(cLin, "piTrocaEmpresa")             > 0 THEN NEXT.
                IF  INDEX(cLin, "piDefineImpressora")         > 0 THEN NEXT.
                IF  INDEX(cLin, "OpenProcess")                > 0 THEN NEXT.
                IF  INDEX(cLin, "TerminateProcess")           > 0 THEN NEXT.
                IF  INDEX(cLin, "CloseHandle")                > 0 THEN NEXT.
                IF  INDEX(cLin, "GetLastInputInfo")           > 0 THEN NEXT.
                IF  INDEX(cLin, "GetTickCount")               > 0 THEN NEXT.
                IF  INDEX(cLin, "guardaValoresNaSessao")      > 0 THEN NEXT.
            END.
            IF  INDEX(cLin, "men/men906za.p") > 0 THEN DO:
                IF  INDEX(cLin, "verifyLicense")       > 0 THEN NEXT.
                IF  INDEX(cLin, "sendSocketData")      > 0 THEN NEXT.
                IF  INDEX(cLin, "readProcedure")       > 0 THEN NEXT.
                IF  INDEX(cLin, "protocolBroker")      > 0 THEN NEXT.
                IF  INDEX(cLin, "piValidaTimeout")     > 0 THEN NEXT.
                IF  INDEX(cLin, "sendToFlex")          > 0 THEN NEXT.
                IF  INDEX(cLin, "ExtendedModeLog")     > 0 THEN NEXT.
                IF  INDEX(cLin, "piCalculaUtilizacao") > 0 THEN NEXT.
                IF  INDEX(cLin, "hasActiveDialogBox")  > 0 THEN NEXT.
                IF  INDEX(cLin, "doLog")               > 0 THEN NEXT.
                IF  INDEX(cLin, "4GL FRM ")            > 0 THEN NEXT. 
            END.
        END.

        /* LS */
        IF  lLS = TRUE THEN DO:
            IF  INDEX(cLin, "btb/btb432za.p") > 0 THEN NEXT.
            IF  INDEX(cLin, "btb/btb432zg.p") > 0 THEN NEXT.
            IF  INDEX(cLin, "btb/btb970aa.p") > 0 THEN NEXT.
            IF  INDEX(cLin, " LS MSG ")       > 0 THEN NEXT.
            IF  INDEX(cLin, "instLicManager") > 0 THEN NEXT.
            IF  INDEX(cLin, "licManagerLoc")  > 0 THEN NEXT.
            IF  INDEX(cLin, "btb/btb970aa.p") > 0 THEN NEXT.
            IF  INDEX(cLin, "licManagerLoc")  > 0 THEN NEXT.
            IF  INDEX(cLin, "licManagerLoc")  > 0 THEN NEXT.
        END.

        /* templates ddk */
        IF  lDDK = TRUE THEN DO:
            IF  INDEX(cLin, "utp/ut-log.p")         > 0 THEN NEXT.
            IF  INDEX(cLin, "Run utp/ut-osver.p ")  > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-cmdln.p")       > 0 THEN NEXT.
            IF  INDEX(cLin, "mlutp/ut-genxml.p")    > 0 THEN NEXT.
            IF  INDEX(cLin, "xmlutp/normalize.p")   > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/windowstyles.p")   > 0 THEN NEXT.
            IF  INDEX(cLin, "adm/objects/broker.p") > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-trata-state")       > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/showmessage.w")    > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/thinfolder.w")     > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-win.p")         > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-style.p")       > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-func.p")        > 0 THEN NEXT.
            IF  INDEX(cLin, "utp/ut-extra.p")       > 0 THEN NEXT.
            IF  INDEX(cLin, "pi-troca-pagina")      > 0 THEN NEXT.
            IF  INDEX(cLin, "panel/p-navega.w")     > 0 THEN NEXT.
            IF  INDEX(cLin, "panel/p-exihel.w")     > 0 THEN NEXT.
            IF  INDEX(cLin, "adm/objects/folder.w") > 0 THEN NEXT.
            IF  INDEX(cLin, "state-changed")        > 0 THEN NEXT.
            IF  INDEX(cLin, "verifySecurity")       > 0 THEN NEXT.
        END.

        /* BOs */
        IF  lDBO = TRUE THEN DO:
            IF  INDEX(cLin, "_selfOthersInfo")     > 0 THEN NEXT.
            IF  INDEX(cLin, "selfInfo")            > 0 THEN NEXT.
            IF  INDEX(cLin, "_copyBuffer2TT")      > 0 THEN NEXT.
            IF  INDEX(cLin, "beforeCopyBuffer2TT") > 0 THEN NEXT.
            IF  INDEX(cLin, "emptyRowObject")      > 0 THEN NEXT.
            IF  INDEX(cLin, "getBatchRecords")     > 0 THEN NEXT.
            IF  INDEX(cLin, "repositionRecord")    > 0 THEN NEXT.
            IF  INDEX(cLin, "emptyRowObjectAux")   > 0 THEN NEXT.
            IF  INDEX(cLin, "_canRunMethod")       > 0 THEN NEXT.
        END.

        /* Fluig */
        IF  lFluig = TRUE 
        AND INDEX(cLin, "fluig") > 0 THEN NEXT.

        /* EAI */
        IF  lEAI = TRUE THEN DO:
            IF  INDEX(cLin, ".eai.")     > 0 THEN NEXT.
            IF  INDEX(cLin, "AS EAI ")   > 0 THEN NEXT.
            IF  INDEX(cLin, "AS EAI2 ")  > 0 THEN NEXT.
            IF  INDEX(cLin, "4GL EAI ")  > 0 THEN NEXT.
            IF  INDEX(cLin, "4GL EAI2 ") > 0 THEN NEXT.
            IF  INDEX(cLin, "WS EAI ")   > 0 THEN NEXT.
            IF  INDEX(cLin, "WS EAI2 ")  > 0 THEN NEXT.
        END.

        /* progress log entry type */
        IF  lProConn = TRUE 
        AND (INDEX(cLin, "4GL CONN") > 0 
        OR   INDEX(cLin, "AS CONN")  > 0
        OR   INDEX(cLin, "WS CONN")  > 0) THEN NEXT.

        IF  lProEvent = TRUE
        AND (INDEX(cLin, "4GL PROEVENTS") > 0
        OR   INDEX(cLin, "AS PROEVENTS")  > 0
        OR   INDEX(cLin, "WS PROEVENTS")  > 0) THEN NEXT.

        IF  lProDyn = TRUE 
        AND (INDEX(cLin, "4GL DYNOBJECTS") > 0
        OR   INDEX(cLin, "AS DYNOBJECTS")  > 0
        OR   INDEX(cLin, "WS DYNOBJECTS")  > 0) THEN NEXT.

        IF  lProTrans = TRUE
        AND INDEX(cLin, "4GLTRANS") > 0 THEN NEXT.

        IF  lProFile = TRUE
        AND (INDEX(cLin, "4GL FILEID") > 0
        OR   INDEX(cLin, "AS FILEID")  > 0
        OR   INDEX(cLin, "WS FILEID")  > 0) THEN NEXT.
        
        IF  lProMsg = TRUE THEN DO:
            IF  INDEX(cLin, "4GL ----------")    > 0 THEN NEXT.
            IF  INDEX(cLin, "AS ----------")     > 0 THEN NEXT.
            IF  INDEX(cLin, "WS ----------")     > 0 THEN NEXT.
            IF  INDEX(cLin, "Logging level set") > 0 THEN NEXT.
            IF  INDEX(cLin, "Log entry types")   > 0 THEN NEXT.
            IF  INDEX(cLin, "4GL 4GLMESSAGE")    > 0 THEN NEXT.
            IF  INDEX(cLin, "AS 4GLMESSAGE")     > 0 THEN NEXT.
            IF  INDEX(cLin, "WS 4GLMESSAGE")     > 0 THEN NEXT.
        END.

        IF  lProTrace = TRUE 
        AND INDEX(cLin, "4GLTRACE") > 0 THEN NEXT.
            
        IF  lProQuery = TRUE 
        AND INDEX(cLin, "QRYINFO") > 0 THEN NEXT.
            
        IF  lProcesso = TRUE 
        AND NUM-ENTRIES(cLin, " ") > 2 THEN DO:
            ASSIGN cProc = ENTRY(2, cLin, " ").
            ASSIGN cArq2 = ENTRY(1,cArq,".") + "_" + cProc + "_clean." + ENTRY(NUM-ENTRIES(cArq, "."),cArq,".").
            OUTPUT stream sDad TO value(cTrgFile + "/" + cArq2) append.
        END.

        PUT STREAM sDad UNFORMATTED
            cLin SKIP.

        IF  lProcesso = TRUE 
        AND NUM-ENTRIES(cLin, " ") > 2 THEN DO:
            OUTPUT stream sDad CLOSE.
        END.
    END.
    INPUT stream sImp CLOSE.
    IF  lProcesso = FALSE THEN 
        OUTPUT stream sDad CLOSE.

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

/* fim */
