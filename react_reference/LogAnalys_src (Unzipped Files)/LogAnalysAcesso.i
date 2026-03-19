/************************************************************************************************
** Procedures para ACESSO do JBoss e Tomcat
************************************************************************************************/

PROCEDURE criaTTAcesso:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hBuffer AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLog:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh", "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcData", "DATE",0,"","","Data").
    ttLog:ADD-NEW-FIELD("tcHora", "CHAR",0,"X(13)","","Hora").
    ttLog:ADD-NEW-FIELD("tcType", "CHAR",0,"x(10)","","Tipo").
    ttLog:ADD-NEW-FIELD("tcTxt",  "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcLinh", "CHAR",0,"x(125)","","URL").
    ttLog:ADD-NEW-FIELD("tcUser", "CHAR",0,"x(15)","","Usuario").
    ttLog:ADD-NEW-FIELD("tcIP",   "CHAR",0,"x(15)","","IP").
    ttLog:ADD-NEW-FIELD("tiResp", "INTE",0,">999","","Resposta").
    ttLog:ADD-NEW-FIELD("tcBytes","CHAR",0,"x(05)","","Bytes").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcIP").
    ttLog:ADD-INDEX-FIELD("codigo", "tcType").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc", "tcIP").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcType").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcData").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcHora").
    ttLog:ADD-INDEX-FIELD("dataProc", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hBuffer = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logAcesso:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE lErros    AS LOGICAL   NO-UNDO LABEL "Somente Erros?"
                                 VIEW-AS TOGGLE-BOX.
    DEFINE VARIABLE cChave    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBrowse   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBuffer   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hTTLog    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE lOrdem    AS LOGICAL   NO-UNDO INITIAL TRUE.

    DEFINE FRAME f-log
        cbTypeLst  AT ROW 01.5 COL 3   LABEL "IP"
        cbCatLst   SPACE(5)
        lErros
        dDatIni    AT ROW 02.5 COL 3
        dDatFim    SPACE(2)
        cHorIni
        cHorFim    SPACE(2)
        cFilter    VIEW-AS FILL-IN SIZE 64 BY 1
        btFilter   btClear
        cDados     NO-LABELS AT ROW 19.5 COL 3
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTAcesso (OUTPUT hTTLog, OUTPUT hBuffer).

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
           DOWN             = 16
           ROW-MARKERS      = FALSE
           VISIBLE          = TRUE
           SENSITIVE        = FALSE
           SEPARATORS       = TRUE
           COLUMN-RESIZABLE = TRUE.

    /* adiciona as colunas do browse */
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiLinh")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcData")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHora")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcUser")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiResp")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcBytes")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcLinh")).

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER   NO-UNDO.
        ASSIGN cbTypeLst
               cbCatLst.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + "_" + cbCatLst + ".log".
        OUTPUT TO VALUE(cArqPrint).
        hQuery:GET-FIRST().
        DO  WHILE NOT hQuery:QUERY-OFF-END:
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE() SKIP.
            hQuery:GET-NEXT().
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  CHOOSE OF btClip IN FRAME f-log DO:
        IF  hBuffer:AVAILABLE THEN
            ASSIGN CLIPBOARD:VALUE = hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE().
    END.

    ON  CHOOSE OF btNotepad IN FRAME f-log DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.

        ASSIGN cbTypeLst
               cbCatLst.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + "_" + cbCatLst + "_tmp.log".
        OUTPUT TO VALUE(cArqPrint).
        PUT UNFORMATTED
           hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()
           SKIP.
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

    ON  VALUE-CHANGED OF cbCatLst, lErros DO:
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
               cbCatLst
               lErros.

        ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcIP = '" + cbTypeLst + "'"
                      + " and ttLog.tcType = '" + cbCatLst + "'"
                      + cChave.

        IF  lErros = TRUE THEN
            ASSIGN cQuery = cQuery + " and ttLog.tiResp > 304".

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
        IF  hBuffer:AVAILABLE THEN
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE().
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

    ASSIGN cDados:READ-ONLY = TRUE
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaAcesso (pDir, pArq, hBuffer).

    ASSIGN cbTypeLst:LIST-ITEMS = getListType().
    IF  CAN-DO(cbTypeLst:LIST-ITEMS, "ERROR") THEN
        ASSIGN cbTypeLst:SCREEN-VALUE = "ERROR".
    ELSE
        ASSIGN cbTypeLst:SCREEN-VALUE = ENTRY(1,cbTypeLst:LIST-ITEMS).

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    APPLY "value-changed" TO cbTypeLst.

    SESSION:SET-WAIT-STATE("").

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-log.
    END.

    FINALLY:
        HIDE FRAME f-log NO-PAUSE.
        hQuery:QUERY-CLOSE().
        DELETE OBJECT hQuery NO-ERROR.
        DELETE OBJECT hTTLog NO-ERROR.
        DELETE OBJECT hBrowse NO-ERROR.
        DELETE OBJECT hBuffer NO-ERROR.
    END.
END PROCEDURE.

PROCEDURE importaAcesso:
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

        ASSIGN cLin = TRIM(cLin).

        RUN criaLinAcesso (cLin, iLinOrg, hBuffer).
    END.
    INPUT STREAM sDad CLOSE.
    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE criaLinAcesso:
    DEFINE INPUT PARAMETER cLin    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cType     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cData     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHora     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cLinS     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE dData     AS DATE      NO-UNDO.
    DEFINE VARIABLE cUser     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cURL      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cIP       AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cResp     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iResp     AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cBytes    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTxt      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cListMes  AS CHARACTER NO-UNDO INITIAL "jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec".

    /* 10.80.73.148 - super [09/Sep/2016:01:40:34 -0300] "GET /menu-html/resources/pulse/getPulseInformation?noCountRequest=true&userCode=super HTTP/1.1" 200 63 */
    ASSIGN cTxt   = cLin
           cLin   = REPLACE(cLin, "-0300] ", "")
           cLin   = TRIM(cLin)
           cIP    = ENTRY(1, cLin, " ")
           cUser  = ENTRY(3, TRIM(cLin), " ")
           cData  = REPLACE(ENTRY(4, cLin, " "), "[", "").
    ASSIGN cHora  = substr(cData, 13, 8)
           cData  = substr(cData, 1, 11)
           cType  = ENTRY(5, cLin, " ")
           cURL   = ENTRY(6, cLin, " ") + " " + entry(7, cLin, " ")
           cResp  = ENTRY(8, cLin, " ")
           cBytes = ENTRY(9, cLin, " ") NO-ERROR.

    IF  cUser = "-" THEN
        ASSIGN cUser = "".
    IF  cBytes = "-" THEN
        ASSIGN cBytes = "".

    /* remove o tipo da linha define o tipo */
    IF  cType BEGINS '"' THEN
        ASSIGN cType = substr(cType, 2, LENGTH(cType)).

    IF  substr(cURL, LENGTH(cURL), 1) = '"' THEN
        ASSIGN cURL = substr(cURL, 1, LENGTH(cURL) - 1).

    IF  cData <> "" THEN
        ASSIGN ENTRY(2, cData, "/") = STRING(LOOKUP(ENTRY(2,cData,"/"),cListMes), "99")
               dData = DATE(cData) no-error.

    ASSIGN iResp = INTEGER(cResp).

    IF  cTxt = ""
    OR  cTxt = ? THEN
        ASSIGN cTxt = cLin.

    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tcData"):BUFFER-VALUE()  = dData.
    hBuffer:BUFFER-FIELD("tcHora"):BUFFER-VALUE()  = cHora.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE()  = cURL.
    hBuffer:BUFFER-FIELD("tcType"):BUFFER-VALUE()  = cType.
    hBuffer:BUFFER-FIELD("tcIP"):BUFFER-VALUE()    = cIP.
    hBuffer:BUFFER-FIELD("tcUser"):BUFFER-VALUE()  = cUser.
    hBuffer:BUFFER-FIELD("tiResp"):BUFFER-VALUE()  = iResp.
    hBuffer:BUFFER-FIELD("tcBytes"):BUFFER-VALUE() = cBytes.
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()   = cTxt NO-ERROR.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()  = iLin.

    RUN criaCateg (cIP, cType).
END PROCEDURE.

/* fim */
