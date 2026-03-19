/************************************************************************************************
** Procedures para TOMCAT
************************************************************************************************/

PROCEDURE criaTTTomcat:
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

PROCEDURE logTomcat:
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
    RUN criaTTTomcat (OUTPUT hTTLog, OUTPUT hBuffer).

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
        AND hBrowse:current-column <> ? THEN
            ASSIGN cQuery = cQuery
                          + " by ttLog." + hBrowse:current-column:name
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

    RUN importaTomcat (pDir, pArq, hBuffer).

    ASSIGN cbTypeLst:LIST-ITEMS = getListType().
    IF  CAN-DO(cbTypeLst:LIST-ITEMS, "ERROR") THEN
        ASSIGN cbTypeLst:SCREEN-VALUE = "ERROR".
    ELSE
        IF  CAN-DO(cbTypeLst:LIST-ITEMS, "SEVERE") THEN
            ASSIGN cbTypeLst:SCREEN-VALUE = "SEVERE".
        ELSE
            ASSIGN cbTypeLst:SCREEN-VALUE = ENTRY(1,cbTypeLst:LIST-ITEMS).

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    APPLY "value-changed" TO cbTypeLst.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.

    FIND FIRST ttFix NO-LOCK NO-ERROR.
    IF  AVAILABLE ttFix THEN
        PUBLISH "showMessage" FROM THIS-PROCEDURE ("Dica: Consegui identificar alguns problemas, clique no botao 'Identifcar Problemas' para analisa-los.").

    ASSIGN btCorrigir:visible = (AVAILABLE ttFix).

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

PROCEDURE importaTomcat:
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

    RUN processaTomcat (hBuffer).

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE processaTomcat:
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
        /* informacoes do ambiente */
        RUN verifyInfoTomcat (ttLin.tcLinh).

        IF  INDEX(ttLin.tcLinh, " INFO [")  > 0
        OR  INDEX(ttLin.tcLinh, " SEVERE [") > 0
        OR  INDEX(ttLin.tcLinh, " WARNING [")  > 0 THEN DO:
            ASSIGN cLin2 = ttLin.tcLinh
                   ix    = 1.
            FOR EACH bfLin EXCLUSIVE-LOCK
                WHERE bfLin.tiLinh > ttLin.tiLinh:
                IF  INDEX(ENTRY(1, TRIM(bfLin.tcLinh), " "), "-" + cAno)  > 0
                OR  INDEX(ENTRY(1, TRIM(bfLin.tcLinh), " "), "-" + cAnoA) > 0 THEN
                    LEAVE.
                ASSIGN cLin2 = cLin2
                             + (IF  cLin2 <> "" THEN CHR(10) ELSE "")
                             + bfLin.tcLinh.
                IF  LENGTH(cLin2) > 15000 THEN DO:
                    createTTDetail (cLin2, ttLin.tiLinh, ix).
                    ASSIGN ix    = ix + 1
                           cLin2 = "".
                END.
                DELETE bfLin.
            END.
            IF  LENGTH(cLin2) > 0 THEN DO:
                createTTDetail (cLin2, ttLin.tiLinh, ix).
                ASSIGN ix    = ix + 1
                       cLin2 = "".
            END.
            RUN criaLinTomcat ("", ttLin.tcLinh, "", ttLin.tiLinh, hBuffer).
            DELETE ttLin.
            NEXT.
        END.

        IF  INDEX(ttLin.tcLinh, "-" + cAno)  = 0
        AND INDEX(ttLin.tcLinh, "-" + cAnoA) = 0 THEN DO:
            DELETE ttLin.
            NEXT.
        END.

        RUN criaLinTomcat ("", ttLin.tcLinh, ttLin.tcLinh, ttLin.tiLinh, hBuffer).
        DELETE ttLin.
    END.

    RUN atualizaFix.
END PROCEDURE.

PROCEDURE criaLinTomcat:
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
    DEFINE VARIABLE cListMes  AS CHARACTER NO-UNDO INITIAL "jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec".

    /* define o tipo */
    IF  INDEX(cLin, " ERROR [") > 0 THEN
        ASSIGN cType = "ERROR"
               cLin = REPLACE(cLin, "ERROR ", "").
    IF  INDEX(cLin, " INFO [") > 0 THEN
        ASSIGN cType = "INFO"
               cLin = REPLACE(cLin, "INFO ", "").
    IF  INDEX(cLin, " WARNING [") > 0 THEN
        ASSIGN cType = "WARN"
               cLin = REPLACE(cLin, "WARNING ", "").
    IF  INDEX(cLin, " DEBUG ") > 0 THEN
        ASSIGN cType = "DEBUG"
               cLin = REPLACE(cLin, "DEBUG ", "").
    IF  INDEX(cLin, " SEVERE [") > 0 THEN
        ASSIGN cType = "SEVERE"
               cLin = REPLACE(cLin, "SEVERE ", "").
    IF  cCateg = ""THEN
        ASSIGN cCateg = cType.

    ASSIGN cLin  = REPLACE(cLin, "[STDERR] ", "")
           cData = ENTRY(1, cLin, " ")
           cHora = ENTRY(2, cLin, " ")
           ENTRY(2, cLin, " ") = ""
           ENTRY(1, cLin, " ") = ""
           cLin = TRIM(cLin).
    IF  cData <> "" THEN
        ASSIGN cData = REPLACE(cData, "-", "/")
               ENTRY(2, cData, "/") = STRING(LOOKUP(ENTRY(2,cData,"/"),cListMes), "99")
               dData = DATE(cData) no-error.


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

PROCEDURE verifyInfoTomcat:
    DEFINE INPUT PARAMETER cLin   AS CHARACTER NO-UNDO.

    /* versao do servidor - 08-Sep-2016 07:58:03.282 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log Server version:        Apache Tomcat/9.0.0.M3 */
    checkInfo(cLin, "Server version:", "[main]", "Versao Servidor").

    /* versao do servidor - 08-Sep-2016 07:58:03.285 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log OS Name:               Windows 8.1 */
    checkInfo(cLin, "OS Name:",        "[main]", "Sistema Operacional").

    /* versao do SO - 08-Sep-2016 07:58:03.285 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log OS Version:            6.3 */
    checkInfo(cLin, "OS Version:",     "[main]", "Versao Sist.Oper.").

    /* arquitetura SO - 08-Sep-2016 07:58:03.286 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log Architecture:          amd64 */
    checkInfo(cLin, "Architecture:",   "[main]", "Arquitetura SO").

    /* java home - 08-Sep-2016 07:58:03.286 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log Java Home:             C:\Program Files\Java\jdk1.8.0_101\jre */
    checkInfo(cLin, "Java Home:",      "[main]", "JAVA_HOME").

    /* JAVA Version - 08-Sep-2016 07:58:03.286 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log JVM Version:           1.8.0_101-b13 */
    checkInfo(cLin, "JVM Version:",   "[main]", "Versao Java").

    /* CATALINA_HOME - 08-Sep-2016 07:58:03.287 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log CATALINA_HOME:         C:\Users\roger.steuernagel\TOTVS\ProgFile\Apache\apache-tomcat-9.0.0.M3 */
    checkInfo(cLin, "CATALINA_HOME:", "[main]", "CATALINA_HOME").

    /* Xms - 08-Sep-2016 07:58:03.287 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log Command line argument: -Xms48m */
    checkInfo(cLin, "Command line argument: -Xms", "[main]", "Memoria -Xms").

    /* Xmx - 08-Sep-2016 07:58:03.288 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log Command line argument: -Xmx256M */
    checkInfo(cLin, "Command line argument: -Xmx", "[main]", "Memoria -Xmx").

    /* MaxPermSize - 08-Sep-2016 07:58:03.288 INFO [main] org.apache.catalina.startup.VersionLoggerListener.log Command line argument: -XX:MaxPermSize=128m */
    checkInfo(cLin, "-XX:MaxPermSize=", "[main]", "Memoria MaxPermSize").
END PROCEDURE.

PROCEDURE verifyFixTomcat:
    DEFINE INPUT PARAMETER cLin   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin   AS INTEGER   NO-UNDO.

    DEFINE VARIABLE cTmp1         AS CHARACTER NO-UNDO.
/*
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
    /* Fix 5 - problemas com appserver */
    IF  INDEX(cLin,"com.datasul.framework.dcl.exception.DatasulRuntimeException: Erro ao obter conexao") > 0
    OR  INDEX(cLin,"Could not create connection; - nested throwable: (java.sql.SQLException:") > 0 THEN DO:
        RUN criaFix("Encontrado um problema com o appserver que nao esta conectando.",
                    "Verifique a configuracao do appserver esta correta no arquivo conf\datasul\datasul_framework.properties ou se o servico do appserver esta disponivel e carregado.",
                    iLin).
    END.
    */
END PROCEDURE.

/* fim */
