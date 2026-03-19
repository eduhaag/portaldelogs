/************************************************************************************************
** Procedures para JBOSS
************************************************************************************************/

PROCEDURE criaTTJBoss:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hLogBuf AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLog:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh", "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcData", "DATE",0,"","","Data").
    ttLog:ADD-NEW-FIELD("tcHora", "CHAR",0,"X(13)","","Hora").
    ttLog:ADD-NEW-FIELD("tcType", "CHAR",0,"x(10)","","Tipo").
    ttLog:ADD-NEW-FIELD("tcTxt",  "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcLinh", "CHAR",0,"x(125)","","Conteudo").
    ttLog:ADD-NEW-FIELD("tcCate", "CHAR",0,"x(20)","","Categoria").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcType").
    ttLog:ADD-INDEX-FIELD("codigo", "tcCate").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc", "tcCate").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcType").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcData").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcHora").
    ttLog:ADD-INDEX-FIELD("dataProc", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hLogBuf = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logJboss:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cChave    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBrowse   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBuffer   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hTTLog    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE lOrdem    AS LOGICAL   NO-UNDO INITIAL TRUE.

    DEFINE QUERY qDetail FOR ttDetail.

    DEFINE BROWSE bDetail QUERY qDetail DISPLAY
        ttDetail.tiSeq
        WITH 7 DOWN size 15 by 8.

    DEFINE FRAME f-log
        cbTypeLst  AT ROW 01.5 COL 3
        cbCatLst
        btInfo     AT ROW 01.5 COL 125
        btCorrigir AT ROW 01.5 COL 152
        dDatIni    AT ROW 02.5 COL 3
        dDatFim    SPACE(2)
        cHorIni
        cHorFim    SPACE(2)
        cFilter    VIEW-AS FILL-IN SIZE 64 BY 1
        btFilter   btClear
        bDetail    AT ROW 19.5 COL 3
        cDados     NO-LABELS AT ROW 19.5 COL 18
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTJBoss (OUTPUT hTTLog, OUTPUT hBuffer).

    /* cria a query */
    CREATE QUERY hQuery.
    hQuery:SET-BUFFERS(hBuffer).

    /* define o browse */
    CREATE BROWSE hBrowse
        ASSIGN
           FRAME            = FRAME f-log:HANDLE
           QUERY            = hQuery
           COL              = 3.00
           ROW              = 4.00
           WIDTH            = 170
           DOWN             = 17
           VISIBLE          = YES
           SENSITIVE        = NO
           SEPARATORS       = TRUE
           COLUMN-RESIZABLE = TRUE.

    /* adiciona as colunas do browse */
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiLinh")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcData")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHora")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcLinh")).

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        ASSIGN cbTypeLst
               cbCatLst.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + "_" + cbCatLst + ".log".
        OUTPUT TO VALUE(cArqPrint).
        hQuery:GET-FIRST().
        DO  WHILE NOT hQuery:QUERY-OFF-END:
            FOR EACH ttDetail NO-LOCK
                WHERE ttDetail.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE():
                PUT UNFORMATTED
                    ttDetail.tcLinh SKIP.
            END.
            hQuery:GET-NEXT().
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  CHOOSE OF btClip IN FRAME f-log DO:
        DEFINE BUFFER bfDet FOR ttDetail.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.
        FIND FIRST bfDet
            WHERE bfDet.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()
            NO-LOCK NO-ERROR.
        IF  AVAILABLE bfDet THEN
            ASSIGN CLIPBOARD:VALUE = bfDet.tcLinh.
        ELSE
            ASSIGN CLIPBOARD:VALUE = "".
    END.

    ON  CHOOSE OF btNotepad IN FRAME f-log DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        DEFINE BUFFER bfDet FOR ttDetail.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.

        ASSIGN cbTypeLst
               cbCatLst.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + "_" + cbCatLst + "_tmp.log".
        OUTPUT TO VALUE(cArqPrint).
        FOR EACH bfDet NO-LOCK
            WHERE bfDet.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE():
            PUT UNFORMATTED
                bfDet.tcLinh SKIP.
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  VALUE-CHANGED OF cbTypeLst DO:
        ASSIGN cbTypeLst
               cbCatLst.
        ASSIGN cbCatLst:LIST-ITEMS = getListCateg(cbTypeLst).
        IF  CAN-DO(cbCatLst:LIST-ITEMS, "ERROR") THEN
            ASSIGN cbCatLst:SCREEN-VALUE = "ERROR".
        ELSE
            ASSIGN cbCatLst:SCREEN-VALUE = ENTRY(1,cbCatLst:LIST-ITEMS).
        APPLY "value-changed" TO cbCatLst.
    END.

    ON  VALUE-CHANGED OF cbCatLst DO:
        ASSIGN lOrdem = TRUE.
        APPLY "recall" TO FRAME f-log.
    END.

    ON  MOUSE-SELECT-CLICK OF hBrowse DO:
        IF  hBuffer:AVAILABLE
        AND hBrowse:CURRENT-COLUMN <> ? THEN
            APPLY "recall" TO FRAME f-log.
    END.

    ON  RECALL OF FRAME f-log DO:
        DEFINE VARIABLE cQuery AS CHARACTER NO-UNDO.

        ASSIGN cbTypeLst
               cbCatLst.

        ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcType = '" + cbTypeLst + "'"
                      + " and ttLog.tcCate = '" + cbCatLst + "'"
                      + cChave.

        IF  hBuffer:AVAILABLE
        AND hBrowse:CURRENT-COLUMN <> ? THEN
            ASSIGN cQuery = cQuery
                          + " by ttLog." + hBrowse:CURRENT-COLUMN:name
                          + (IF lOrdem THEN " desc" ELSE "")
                   lOrdem = NOT lOrdem.

        hQuery:QUERY-CLOSE().

        hQuery:QUERY-PREPARE(cQuery).

        hQuery:QUERY-OPEN().
        APPLY "VALUE-CHANGED" TO hBrowse.
        APPLY "entry" TO hBrowse.
    END.

    ON  VALUE-CHANGED OF hBrowse DO:
        IF  NOT hBuffer:AVAILABLE THEN DO:
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = "".
            RETURN.
        END.
        OPEN QUERY qDetail
            FOR EACH ttDetail
                WHERE ttDetail.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE().
        APPLY "value-changed" TO bDetail.
    END.

    ON  VALUE-CHANGED OF bDetail DO:
        IF  AVAILABLE ttDetail THEN
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = ttDetail.tcLinh.
        ELSE
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = "".
    END.

    ON  CHOOSE OF btClear DO:
        ASSIGN cFilter:SCREEN-VALUE = ""
               cChave = "".
        APPLY "value-changed" TO cbCatLst.
    END.

    ON  CHOOSE OF btFilter
    OR  RETURN OF cFilter, dDatIni, dDatFim, cHorIni, cHorFim DO:
        ASSIGN cFilter
               dDatIni
               dDatFim
               cHorIni
               cHorFim.

        ASSIGN cChave = "".
        IF  cFilter <> ""
        AND cFilter <> ? THEN
            ASSIGN cChave = cChave + " and ttLog.tcLinh matches '*" + cFilter + "*'".

        IF  dDatIni <> 01/01/1800
        OR  dDatFim <> 12/31/9999 THEN
            ASSIGN cChave = cChave
                          + " and ttLog.tcData >= " + string(dDatIni,"99/99/9999")
                          + " and ttLog.tcData <= " + string(dDatFim,"99/99/9999").

        IF  cHorIni <> "000000"
        OR  cHorFim <> "999999" THEN
            ASSIGN cChave = cChave
                          + " and ttLog.tcHora >= '" + string(cHorIni,"99:99:99") + ",000'"
                          + " and ttLog.tcHora <= '" + string(cHorFim,"99:99:99") + ",999'".

        APPLY "value-changed" TO cbCatLst.
    END.

    ON  CHOOSE OF btCorrigir DO:
        RUN showFix (cDir, cArq).
    END.

    ON  CHOOSE OF btInfo DO:
        RUN showInfo.
    END.

    ASSIGN cDados:READ-ONLY = TRUE
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse
           hDet             = BROWSE bDetail:handle.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaJboss (pDir, pArq, hBuffer).

    ASSIGN cbTypeLst:LIST-ITEMS = getListType().
    IF  CAN-DO(cbTypeLst:LIST-ITEMS, "ERROR") THEN
        ASSIGN cbTypeLst:SCREEN-VALUE = "ERROR".
    ELSE
        ASSIGN cbTypeLst:SCREEN-VALUE = ENTRY(1,cbTypeLst:LIST-ITEMS).

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    APPLY "value-changed" TO cbTypeLst.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.

    FIND FIRST ttFix NO-LOCK NO-ERROR.
    IF  AVAILABLE ttFix THEN
        PUBLISH "showMessage" FROM THIS-PROCEDURE ("Dica: Consegui identificar alguns problemas, clique no botao 'Identifcar Problemas' para analisa-los.").

    ASSIGN btCorrigir:visible = (AVAILABLE ttFix)
           btInfo:visible     = (cInfo <> "" AND cInfo <> ?).

    FIND FIRST ttInfo NO-LOCK NO-ERROR.
    ASSIGN btInfo:visible = (AVAILABLE ttInfo).

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-log.
    END.

    FINALLY:
        HIDE MESSAGE NO-PAUSE.
        HIDE FRAME f-log NO-PAUSE.
        hQuery:QUERY-CLOSE().
        DELETE OBJECT hBrowse NO-ERROR.
        DELETE OBJECT hQuery NO-ERROR.
        DELETE OBJECT hBuffer NO-ERROR.
        DELETE OBJECT hTTLog NO-ERROR.
    END.
END PROCEDURE.

PROCEDURE importaJboss:
    DEFINE INPUT PARAMETER cDir    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cArq    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cArq2     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iLinOrg   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iFileLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iProcLen  AS INTEGER   NO-UNDO.

    RUN zeraTT (hBuffer).

    ASSIGN FILE-INFO:FILENAME = cDir + cArq
           iFileLen           = FILE-INFO:FILE-SIZE
           cInfo              = "".

    ASSIGN cArq2 = ENTRY(1,cArq,".") + "_novo." + ENTRY(2,cArq,".").

    INPUT STREAM sDad FROM VALUE(cDir + cArq).
    REPEAT:
        ASSIGN iLinOrg = iLinOrg + 1.
        IMPORT STREAM sDad UNFORMATTED cLin NO-ERROR.
        IF  ERROR-STATUS:ERROR = TRUE THEN
            LEAVE.

        ASSIGN iProcLen = iProcLen + length(cLin).

        IF  TRIM(cLin) = "" THEN
            NEXT.

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.

        CREATE ttLin.
        ASSIGN ttLin.tcLinh = cLin
               ttLin.tiLinh = iLinOrg.
    END.
    INPUT STREAM sDad CLOSE.

    RUN processaJboss (hBuffer).

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE processaJboss:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE iLinTot   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE ix        AS INTEGER   NO-UNDO.

    DEFINE BUFFER bfLin FOR ttLin.

    FIND LAST ttLin NO-LOCK NO-ERROR.
    IF  AVAILABLE ttLin THEN
        ASSIGN iLinTot = ttLin.tiLinh.
        
    FOR EACH ttLin EXCLUSIVE-LOCK:
        IF  (ttLin.tiLinh MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Processando " + STRING(ttLin.tiLinh, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iLinTot, "zzz,zzz,zzz,zzz,zz9") + " linhas.").
        END.
        ASSIGN cLin = ttlin.tcLinh.

        IF  NOT TRIM(cLin) BEGINS cAno
        AND NOT TRIM(cLin) BEGINS cAnoA THEN DO:
            IF  TRIM(cLin) BEGINS "Reason:" THEN DO:
                RUN verifyFixJboss (cLin, ttLin.tiLinh).
                createTTDetail (cLin, ttLin.tiLinh, 1).
                RUN criaLinJboss ("ERROR", cLin, cLin, ttLin.tiLinh, hBuffer).
            END.
            DELETE ttLin.
            NEXT.
        END.

        /* informacoes do ambiente */
        RUN verifyInfoJboss (cLin).

        IF  INDEX(cLin, " ERROR [")  > 0
        OR  INDEX(cLin, " SEVERE [") > 0
        OR  INDEX(cLin, " WARN  [")  > 0 THEN DO:
            IF  INDEX(cLin, "log4j:") = 0 THEN DO:
                ASSIGN cLin2 = cLin.
                       ix    = 1.
                /* verifica se existe fix para o problema */
                RUN verifyFixJboss (cLin, ttLin.tiLinh).
                FOR EACH bfLin EXCLUSIVE-LOCK
                    WHERE bfLin.tiLinh > ttLin.tiLinh:
                    ASSIGN cLin3 = bfLin.tcLinh.

                    IF  TRIM(cLin3) = "" THEN DO:
                        DELETE bfLin.
                        NEXT.
                    END.
                    IF  TRIM(cLin3) BEGINS "State:"
                    AND INDEX(cLin3, "INIT_WAITING_DEPLOYER") = 0 THEN
                        LEAVE.

                    /* verifica se existe fix para o problema */
                    RUN verifyFixJboss (cLin3, ttLin.tiLinh).

                    IF  (INDEX(cLin3, " ERROR [STDERR] ") > 0
                    AND (TRIM(cLin3) BEGINS cAno
                    OR   TRIM(cLin3) BEGINS cAnoA)) THEN DO:
                        ASSIGN cLin3   = REPLACE(cLin3, "ERROR [STDERR] ", "")
                               cLin2   = cLin2
                                       + (IF  cLin2 <> "" THEN CHR(10) ELSE "")
                                       + cLin3.
                        DELETE bfLin.
                        NEXT.
                    END.

                    IF  TRIM(cLin3) BEGINS cAno
                    OR  TRIM(cLin3) BEGINS cAnoA
                    OR  NUM-ENTRIES(ENTRY(1, cLin3, " "),":") > 2 THEN
                        LEAVE.

                    ASSIGN cLin2 = cLin2
                                 + (IF  cLin2 <> "" THEN CHR(10) ELSE "")
                                 + cLin3.
                    IF  LENGTH(cLin2) > 15000 THEN DO:
                        createTTDetail (cLin2, ttLin.tiLinh, ix).
                        ASSIGN ix    = ix + 1
                               cLin2 = "".
                    END.
                    DELETE bfLin.
                END.
                RUN verifyInfoJboss (cLin3).
                IF  LENGTH(cLin2) > 0 THEN DO:
                    createTTDetail (cLin2, ttLin.tiLinh, ix).
                    ASSIGN ix    = ix + 1
                           cLin2 = "".
                END.
                RUN criaLinJboss ("ERROR", ttLin.tcLinh, "", ttLin.tiLinh, hBuffer).
            END.
            DELETE ttLin.
            NEXT.
        END.

        ASSIGN cLin = TRIM(cLin).

        /* ignora varios itens do log */
        /* josso */
        IF  INDEX(cLin, "[org.josso.gateway.session.") > 0
        OR  INDEX(cLin, "[org.josso.jb42.agent.") > 0
        OR  INDEX(cLin, "[org.josso.tc55.agent.") > 0
        OR  INDEX(cLin, "[org.josso.Lookup]") > 0
        OR  INDEX(cLin, "[org.josso.ComponentKeeperImpl]") > 0
        OR  INDEX(cLin, "[org.josso.MBeanComponentKeeper]") > 0
        OR  INDEX(cLin, "[org.josso.ComponentKeeperImpl]") > 0
        OR  INDEX(cLin, "[org.josso.MBeanComponentKeeper]") > 0
        OR  INDEX(cLin, "[org.josso.gateway.") > 0

        /* jboss */
        OR  INDEX(cLin, "[org.jboss.") > 0
        OR  INDEX(cLin, "[com.arjuna.ats.") > 0
        OR  INDEX(cLin, "[org.jnp.server.") > 0
        OR  INDEX(cLin, "[org.apache.") > 0
        OR  INDEX(cLin, "[org.quartz.") > 0
        OR  INDEX(cLin, "[org.ajax4jsf.") > 0
        OR  INDEX(cLin, "[net.sf.") > 0
        /* hibernate */
        OR  (INDEX(cLin, "[org.hibernate.") > 0
        AND  INDEX(cLin, "QueryTranslatorImpl] HQL:") = 0)
        /* totvs */
        OR  INDEX(cLin, "[com.datasul.framework.dcl.persistence.") > 0
        OR  INDEX(cLin, "[com.datasul.sop.customization.CustomizationBO]") > 0
        OR  INDEX(cLin, "[STDOUT] HASH - []") > 0
        OR  INDEX(cLin, "[TOTVSMonitor]") > 0 THEN DO:
            DELETE ttLin.
            NEXT.
        END.

        IF  INDEX(cLin, "INFO  [STDOUT]") > 0
        AND TRIM(ENTRY(2, cLin, "]")) = ""  THEN DO:
            DELETE ttLin.
            NEXT.
        END.

        RUN criaLinJboss ("", cLin, cLin, ttLin.tiLinh, hBuffer).
        createTTDetail (cLin, ttLin.tiLinh, 1).
    END.

    RUN atualizaFix.
END PROCEDURE.

PROCEDURE criaLinJboss:
    DEFINE INPUT PARAMETER cCateg  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cLin    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cTxt    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cType     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cData     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHora     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cLinS     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE dData     AS DATE      NO-UNDO.

    /* define o tipo */
    IF  INDEX(cLin, " ERROR [") > 0 THEN
        ASSIGN cType = "ERROR"
               cLin = REPLACE(cLin, " ERROR [", " [").
    IF  INDEX(cLin, " INFO  [") > 0 THEN
        ASSIGN cType = "INFO"
               cLin = REPLACE(cLin, " INFO  [", " [").
    IF  INDEX(cLin, " WARN  [") > 0 THEN
        ASSIGN cType = "WARN"
               cLin = REPLACE(cLin, " WARN  [", " [").
    IF  INDEX(cLin, " DEBUG ") > 0 THEN
        ASSIGN cType = "DEBUG"
               cLin = REPLACE(cLin, " DEBUG ", " ").
    IF  cCateg = "Error"
    AND cType = "" THEN
        ASSIGN cType = "ERROR".

    ASSIGN cLin  = REPLACE(cLin, "[STDERR] ", "")
           cData = ENTRY(1, cLin, " ")
           cHora = ENTRY(2, cLin, " ")
           ENTRY(2, cLin, " ") = ""
           ENTRY(1, cLin, " ") = ""
           cLin = TRIM(cLin).

    /* define as categorias */
    IF  INDEX(cLin, "[com.totvs.license.client.LicenseClientDelegate]") > 0
    OR  INDEX(cLin, "[FlexLicenseServlet]") > 0 THEN DO:
        ASSIGN cCateg = "LICENSE"
               cLinS  = cLin
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").
        IF  cLin = "" THEN
            ASSIGN cLin = cLinS.
    END.

    IF  INDEX(cLin, "[com.totvs.license]") > 0 THEN
        ASSIGN cCateg = "LICENSE PULSE"
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").

    IF  INDEX(cLin, "[com.totvs.datasul.ekanban.") > 0
    OR  INDEX(cLin, "ERROR [DatasulService] com.datasul.service.genericerror") > 0 THEN
        ASSIGN cCateg = "BUSINESS".

    IF  INDEX(cLin, "[com.datasul.framework.josso.jboss.auth.DatasulAuthenticatorImpl]") > 0 THEN
        ASSIGN cCateg = "Authentication"
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").

    IF  INDEX(cLin, "[com.datasul.eip.flex.session.") > 0
    OR  INDEX(cLin, "[org.josso.gateway.audit.SSO_AUDIT]") > 0
    OR  INDEX(cLin, "[EIPFlexServerSessionManagerHTML]") > 0
    OR  INDEX(cLin, "[com.datasul.framework.menu.servlet.JMSServlet]") > 0 THEN DO:
        IF  NUM-ENTRIES(cLin, "[") = 3
        AND ENTRY(1, cLin, "[") BEGINS "STDOUT" THEN
            ASSIGN ENTRY(2, clin, "[") = ""
                   cLin = REPLACE(cLin, "[[", "[").
        ASSIGN cCateg = "SESSION"
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").
    END.

    IF  INDEX(cLin, "[com.datasul.framework.dcl.i18n.") > 0 THEN
        ASSIGN cCateg = "TRANSLATION"
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").

    IF  INDEX(cLin, "[org.hibernate.hql.ast.QueryTranslatorImpl]") > 0 THEN
        ASSIGN cCateg = "DB.ACCESS"
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").

    IF  INDEX(cLin, "[com.datasul.framework.security.DatasulCachePolicyService]") > 0 THEN
        ASSIGN cCateg = "CACHE"
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").

    IF  INDEX(cLin, "[com.datasul.framework.dcl.util.PropertyUtil]") > 0 THEN
        ASSIGN cCateg = "PROPERTY"
               cLin   = REPLACE(cLin, "[" + entry(1, ENTRY(2, cLin, "["), "]") + "]", "").

    IF  INDEX(cLin, " DEBUG ") > 0 THEN
        ASSIGN cCateg = "DEBUG".

    IF  cCateg = "" THEN
        ASSIGN cCateg = "DIVERSOS".

     IF  INDEX(cLin, "FLUIG_") > 0 THEN
        ASSIGN cCateg = "FLUIG".

    IF  NUM-ENTRIES(cData, "-") > 1 THEN DO:
        ASSIGN dData = DATE(ENTRY(3, cData, "-") + "/" + entry(2, cData, "-") + "/" + entry(1, cData, "-")) no-error.
        IF  ERROR-STATUS:ERROR = TRUE THEN
            ASSIGN dData = TODAY.
    END.

    IF  cTxt = ""
    OR  cTxt = ? THEN
        ASSIGN cTxt = cLin.

    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tcData"):BUFFER-VALUE() = dData.
    hBuffer:BUFFER-FIELD("tcHora"):BUFFER-VALUE() = cHora.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE() = cLin.
    hBuffer:BUFFER-FIELD("tcType"):BUFFER-VALUE() = cType.
    hBuffer:BUFFER-FIELD("tcCate"):BUFFER-VALUE() = cCateg.
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()  = cTxt.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() = iLin.

    RUN criaCateg (cType, cCateg).
END PROCEDURE.

PROCEDURE verifyInfoJboss:
    DEFINE INPUT PARAMETER cLin   AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cTmp1     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTmp2     AS CHARACTER NO-UNDO.

    /* versao do produto */
    IF  INDEX(cLin, "/datasul-byyou-") > 0
    AND INDEX(cLin, ".ear") > 0
    AND INDEX(cInfo, "Versao Produto") = 0 THEN DO:
        ASSIGN cTmp1 = REPLACE(substr(cLin, INDEX(cLin, "/datasul-byyou-"), LENGTH(cLin)), "/datasul-byyou-", "")
               cTmp1 = substr(cTmp1, 1, INDEX(cTmp1, ".ear") - 1)
               cInfo = cInfo + "Versao Produto...: " + trim(cTmp1) + chr(10).
    END.
    /* versao do LS */
    IF  INDEX(cLin, "Connector version:") > 0
    AND INDEX(cInfo, "Versao LS") = 0 THEN DO:
        ASSIGN cTmp1 = substr(cLin, INDEX(cLin, "Connector version:"), LENGTH(cLin))
               cTmp1 = ENTRY(2, cTmp1, ":")
               cTmp1 = REPLACE(cTmp1, "#", "")
               cInfo = cInfo + "Versao LS........: " + trim(cTmp1) + chr(10).
    END.
    /* servidor LS */
    IF  INDEX(cLin, "# LS IP") > 0
    AND INDEX(cInfo, "Servidor LS") = 0 THEN DO:
        ASSIGN cTmp1 = substr(cLin, INDEX(cLin, "# LS IP"), LENGTH(cLin))
               cTmp1 = ENTRY(2, cTmp1, ":")
               cTmp1 = REPLACE(cTmp1, "#", "")
               cInfo = cInfo + "Servidor LS......: " + trim(cTmp1) + chr(10).
    END.
    /* porta LS */
    IF  INDEX(cLin, "# LS Port") > 0
    AND INDEX(cInfo, "Porta LS") = 0 THEN DO:
        ASSIGN cTmp1 = substr(cLin, INDEX(cLin, "# LS Port"), LENGTH(cLin))
               cTmp1 = ENTRY(2, cTmp1, ":")
               cTmp1 = REPLACE(cTmp1, "#", "")
               cInfo = cInfo + "Porta LS.........: " + trim(cTmp1) + chr(10).
    END.
    /* timeout LS */
    IF  INDEX(cLin, "# LS Timeout") > 0
    AND INDEX(cInfo, "Timeout LS") = 0 THEN DO:
        ASSIGN cTmp1 = substr(cLin, INDEX(cLin, "# LS Timeout"), LENGTH(cLin))
               cTmp1 = ENTRY(2, cTmp1, ":")
               cTmp1 = REPLACE(cTmp1, "#", "")
               cInfo = cInfo + "Timeout LS.......: " + trim(cTmp1) + chr(10).
    END.
    /* tipo do LS */
    IF  INDEX(cLin, "# Ambient Type") > 0
    AND INDEX(cInfo, "Tipo Ambiente") = 0 THEN DO:
        ASSIGN cTmp1 = substr(cLin, INDEX(cLin, "# Ambient Type"), LENGTH(cLin))
               cTmp1 = ENTRY(2, cTmp1, ":")
               cTmp1 = REPLACE(cTmp1, "#", "")
               cInfo = cInfo + "Tipo Ambiente....: " + trim(cTmp1) + chr(10).
    END.
    /* tipo e versao de banco */
    IF  INDEX(cLin, "[org.hibernate.cfg.SettingsFactory] RDBMS:") > 0
    AND INDEX(cInfo, "Tipo de Banco") = 0 THEN DO:
        ASSIGN cTmp1 = substr(cLin, INDEX(cLin, "[org.hibernate.cfg.SettingsFactory] RDBMS:"), LENGTH(cLin))
               cTmp2 = ENTRY(3, cTmp1, ":") /* versao */
               cTmp1 = ENTRY(1, ENTRY(2, cTmp1, ":")) /* tipo */
               cInfo = cInfo + "Tipo de Banco....: " + trim(cTmp1) + chr(10)
               cInfo = cInfo + "Versao Banco.....: " + trim(cTmp2) + chr(10).
    END.
    /* tempo de carga do Jboss */
    IF  INDEX(cLin, "JBoss (MX MicroKernel)") > 0
    AND INDEX(cLin, "Started in ") > 0
    AND INDEX(cInfo, "Tempo Carga JBoss") = 0 THEN DO:
        ASSIGN cTmp1 = REPLACE(substr(cLin, INDEX(cLin, "Started in "), LENGTH(cLin)), "Started in ", "")
               cInfo = cInfo + "Tempo Carga JBoss: " + trim(cTmp1) + chr(10).
    END.
    /* porta jboss */
    IF  INDEX(cLin, "[org.apache.coyote.http11.Http11Protocol] Starting Coyote HTTP") > 0
    AND INDEX(cInfo, "Porta JBoss") = 0 THEN DO:
        ASSIGN cTmp1 = TRIM(REPLACE(cLin, "[org.apache.coyote.http11.Http11Protocol] Starting Coyote HTTP", ""))
               cTmp1 = ENTRY(7, cTmp1, " ")
               cInfo = cInfo + "Porta JBoss......: " + trim(cTmp1) + chr(10) no-error.
    END.
END PROCEDURE.

PROCEDURE verifyFixJboss:
    DEFINE INPUT PARAMETER cLin   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin   AS INTEGER   NO-UNDO.

    DEFINE VARIABLE cTmp1         AS CHARACTER NO-UNDO.

    /* Fix 1 - rest.properties */
    IF  INDEX(cLin, "FileNotFoundException") > 0
    AND INDEX(cLin, "null\rest.properties") > 0 THEN DO:
        RUN criaFix("Nao foi possivel localizar o arquivo rest.properties",
                    "Dentro do \conf\datasul\datasul_framework.properties, especifique uma tag 'datasul.rest.dir' contendo um diretorio valido onde o arquivo rest.properties esta localizado."
                    + chr(10) + "Mais informacoes sobre o Datasul REST: http://tdn.totvs.com/pages/viewpage.action?pageId=185750625",
                    iLin).
    END.
    /* Fix 2 - arquivo nao deployado */
    IF  INDEX(cLin, "watch: file:") > 0 THEN DO:
        ASSIGN cTmp1 = TRIM(REPLACE(cLin, "watch: file:", "")).
        RUN criaFix("Arquivo " + cTmp1 + " nao pode ser deployado.",
                    "Verifique se o arquivo esta correto ou deva ser renomeado para '.rej'",
                    iLin).
    END.
    /* Fix 3 - problemas com banco de dados */
    IF  cLin BEGINS "ObjectName: persistence.units"
    AND INDEX(cLin, "unitName=") > 0 THEN DO:
        ASSIGN cTmp1 = ENTRY(2, ENTRY(3, cLin), "=").
        RUN criaFix("Nao foi possivel localizar dentro do arquivo progress-ds.xml ou oracle-ds.xml ou mss-ds.xml, o banco " + cTmp1,
                    "Especifique no arquivo progress-ds.xml ou oracle-ds.xml ou mss-ds.xml a unidade de persistencia para o banco " + cTmp1,
                    iLin).
    END.
    /* Fix 4 - problemas com porta em uso */
    IF  INDEX(cLin, "java.rmi.server.ExportException: Port already in use:") > 0 THEN DO:
        ASSIGN cTmp1 = ENTRY(1, ENTRY(3, cLin, ":"), ";").
        RUN criaFix("Encontrado um problema com a porta " + cTmp1 + " que esta em uso por um outro processo/servico.",
                    "Verifique a porta " + cTmp1 + " que esta em uso por algum outro processo ou servico. Configure corretamente a porta no arquivo conf\jboss-service.xml.",
                    iLin).
    END.
    /* Fix 4a - problemas com porta em uso */
    IF  INDEX(cLin, "Reason: java.")  > 0
    AND index(cLin, "Exception: Port ") > 0 
    AND index(cLin, "already in use")   > 0 THEN DO:
        ASSIGN cTmp1 = REPLACE(ENTRY(3, cLin, ":"), "Port", "")
               cTmp1 = TRIM(REPLACE(cTmp1, "already in use", "")).
        RUN criaFix("Encontrado um problema com a porta " + cTmp1 + " que esta em uso por um outro processo/servico.",
                    "Verifique a porta " + cTmp1 + " que esta em uso por algum outro processo ou servico. Configure corretamente a porta no arquivo conf\jboss-service.xml." + chr(10) + 
                    "Este erro ocorreu no logo apos ser concluido o deploy do produto.",
                    iLin).
    END.
    /* Fix 5 - problemas com appserver */
    IF  INDEX(cLin,"com.datasul.framework.dcl.exception.DatasulRuntimeException: Erro ao obter conexao") > 0
    OR  INDEX(cLin,"Could not create connection; - nested throwable: (java.sql.SQLException:") > 0 THEN DO:
        RUN criaFix("Encontrado um problema com o appserver que nao esta conectando.",
                    "Verifique a configuracao do appserver esta correta no arquivo conf\datasul\datasul_framework.properties ou se o servico do appserver esta disponivel e carregado.",
                    iLin).
    END.
    /* Fix 6 - problemas ao obter a extensao do usuario */
    IF  INDEX(cLin,"com.datasul.framework.menu.service.bussiness.UserMasterExtBO.getCodUserByCodUserSoAndDomain(UserMasterExtBO.java:") > 0 THEN DO:
        RUN criaFix("Encontrado um problema ao obter a extensao do usuario.",
                    "Verifique no cadastro de usuarios (sec000aa), aba Extensoes, se o usuario possui pelo menos uma extensao cadastrada.",
                    iLin).
    END.
    /* Fix 7 - problemas com campos no banco de dados */
    /* 2016-09-14 07:55:46,249 ERROR [org.hibernate.util.JDBCExceptionReporter] [DataDirect][OpenEdge JDBC Driver][OpenEdge] Column cod_release_prog_dtsul in table PUB.ped_exec has value exceeding its max length or precision. */
    IF  INDEX(cLin,"[org.hibernate.util.JDBCExceptionReporter] [DataDirect][OpenEdge JDBC Driver][OpenEdge] Column") > 0 THEN DO:
        RUN criaFix("Encontrado um problema com o banco de dados, onde uma coluna estourou o tamanho maximo.",
                    "Ajuste o tamanho do campo para solucionar este problema.",
                    iLin).
    END.
    
    /* Fix 8 - problemas com campos de temp-tables que nao batem */
    /* 2018-08-24 19:51:20,736 ERROR [STDERR] com.progress.open4gl.RunTime4GLErrorException: ERROR condition: Numero de parametros 1 (table ttOrderDetails) incompativel. Existem 249 campos - o schema do cliente tem 252 campos. (8030) (7211)
       2018-08-24 19:51:20,741 ERROR [STDERR]  at com.progress.open4gl.RunTime4GLException.createException(RunTime4GLException.java:46)
    */
    IF  INDEX(cLin,"com.progress.open4gl.RunTime4GLErrorException: ERROR condition: Numero de parametros") > 0 
    AND INDEX(cLin,"incompativel.") > 0 THEN DO:
        RUN criaFix("Encontrado um problema com o numero de parametros passados para uma temp-table, onde nao estao batendo o numero de campos.",
                    "Verifique se a temp-table esta com o numero correto de campos.",
                    iLin).
    END.
END PROCEDURE.

/* fim */
