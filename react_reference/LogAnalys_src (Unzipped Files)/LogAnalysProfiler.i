/************************************************************************************************
** Procedures para Profiler
************************************************************************************************/

/* Temptable storing the SEARCH lines from the XRef file */
DEFINE TEMP-TABLE ttSearch NO-UNDO
    FIELD sessionid      AS INTEGER
    FIELD srcid          AS INTEGER
    FIELD LineId         AS INTEGER
    FIELD Xref-LineId    AS INTEGER
    FIELD SearchType     AS CHARACTER    /* Can-Find, Find, For-Each */
    FIELD DatabaseName   AS CHARACTER
    FIELD TableName      AS CHARACTER
    FIELD UsedIndexes    AS CHARACTER    /* Comma-separated list */
    FIELD AccessedFields AS CHARACTER    /* Comma-separated list */
    FIELD IndexScore1    AS DECIMAL
    FIELD IndexScore2    AS DECIMAL
    INDEX i1 IS PRIMARY UNIQUE sessionid srcid LineId
    INDEX i2 IndexScore1            /* For Browse Sort */
    INDEX i3 IndexScore2.           /* For Browse Sort */

DEFINE TEMP-TABLE ttSource NO-UNDO
    FIELD srcid            AS INTEGER
    FIELD srcname          AS CHARACTER FORMAT "X(150)" COLUMN-LABEL "Bloco de Codigo"
    FIELD srcfile          AS CHARACTER
    FIELD xreffile         AS CHARACTER
    FIELD parent           AS INTEGER
    FIELD avg_acttime      AS DECIMAL FORMAT ">>9.999999" COLUMN-LABEL "Tempo Medio"
    FIELD tot_acttime      AS DECIMAL
    FIELD tot_parenttime   AS DECIMAL
    FIELD tot_cumtime      AS DECIMAL FORMAT ">>>>,>>>9.999999" COLUMN-LABEL "Tempo Acum"
    FIELD listname         AS CHARACTER
    FIELD session-id       AS INTEGER
    FIELD callcnt          AS INTEGER FORMAT ">>9.999999" COLUMN-LABEL "Chamadas"
    FIELD session-percent  AS DECIMAL FORMAT ">>9.999999" COLUMN-LABEL "% Sessao"
    FIELD percall-percent  AS DECIMAL
    FIELD overhead_time    AS DECIMAL
    FIELD first-line       AS INTEGER
    FIELD total-time       AS DECIMAL FORMAT ">,>>9.999999"     COLUMN-LABEL "Tempo Total"
    FIELD srcexectime      AS DECIMAL  /* total executation time for this procedure and its children */
    FIELD CRC-Val          AS INTEGER
    INDEX sourceid AS PRIMARY UNIQUE session-id srcid
    INDEX sessparent session-id  parent tot_acttime DESCENDING
    INDEX tot-actualtime  session-id  tot_acttime DESCENDING
    INDEX searchbyword AS WORD-INDEX srcname.

DEFINE TEMP-TABLE ttCallTree NO-UNDO
    FIELD caller     AS INTEGER
    FIELD callee     AS INTEGER
    FIELD callcnt    AS INTEGER
    FIELD session-id AS INTEGER
    INDEX caller-callee AS UNIQUE PRIMARY session-id  caller  callee
    INDEX callee session-id  callee.

DEFINE TEMP-TABLE ttTotais NO-UNDO
    FIELD stmtcnt               AS INTEGER COLUMN-LABEL "Exec Count" FORMAT ">>>,>>9"
    FIELD acttime               AS DECIMAL COLUMN-LABEL "Avg Exec"   FORMAT ">,>>9.999999"
    FIELD lineno                AS INTEGER COLUMN-LABEL "Line" FORMAT ">>>,>>9"
    FIELD srcid                 AS INTEGER
    FIELD cumtime               AS DECIMAL
    FIELD tot_cumtime           AS DECIMAL COLUMN-LABEL "Cum Time"   FORMAT ">,>>>9.999999"
    FIELD tot_acttime           AS DECIMAL COLUMN-LABEL "Tot Time"   FORMAT  ">,>>9.999999"
    FIELD session-id            AS INTEGER
    FIELD session-percent       AS DECIMAL
    FIELD perprocedure-percent  AS DECIMAL
    FIELD parent  AS INTEGER
    INDEX actual-time AS PRIMARY session-id acttime
    INDEX cumulative-time session-id  cumtime DESCENDING
    INDEX parent  session-id  parent  lineno
    INDEX src-line  AS UNIQUE session-id  srcid  lineno
    INDEX tottime  session-id  srcid  tot_acttime.

DEFINE TEMP-TABLE ttProfileSession NO-UNDO
    FIELD session-id     AS INTEGER
    FIELD Session-Desc   AS CHARACTER
    FIELD session-date   AS DATE
    FIELD tot_acttime    AS DECIMAL
    FIELD session-notes  AS CHARACTER
    FIELD Session-Time   AS CHARACTER
    FIELD Session-User   AS CHARACTER
    FIELD Session-dir    AS CHARACTER
    FIELD Session-arq    AS CHARACTER
    INDEX sessid  AS UNIQUE PRIMARY session-id.

DEFINE TEMP-TABLE ttCallTreeData NO-UNDO
    FIELD caller       AS INTEGER
    FIELD callee       AS INTEGER
    FIELD callcnt      AS INTEGER
    FIELD session-id   AS INTEGER
    FIELD callerlineno AS INTEGER
    INDEX caller-callee AS PRIMARY session-id   caller  callerlineno  callee
    INDEX callee session-id  callee.

PROCEDURE logProgsProfiler:
    DEFINE BUFFER bfTTCallTree FOR ttCallTree.
    DEFINE BUFFER bfTTCallee   FOR ttSource.
    DEFINE BUFFER bfTTCaller   FOR ttSource.

    DEFINE VARIABLE cFileNameShown   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iLineNumberShown AS INTEGER   NO-UNDO.
    DEFINE VARIABLE deTotalTime      AS DECIMAL   NO-UNDO DECIMALS 6.
    DEFINE VARIABLE iSrcId           AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cLin             AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cbImport         AS CHARACTER NO-UNDO FORMAT "x(40)" LABEL "Importacoes"
                                        VIEW-AS COMBO-BOX INNER-LINES 10 SIZE 40 BY 1.
    DEFINE VARIABLE lStoreData       AS LOGICAL   NO-UNDO LABEL "Acumula Dados Anteriores" INITIAL TRUE
                                        VIEW-AS TOGGLE-BOX.

    DEFINE BUTTON btCompare   LABEL "Comparar".

    DEFINE QUERY qSource FOR ttSource SCROLLING.
    DEFINE QUERY qCaller FOR ttCallTree, bfTTCaller SCROLLING.
    DEFINE QUERY qCallee FOR bfTTCallTree, bfTTCallee SCROLLING.
    DEFINE QUERY qLine   FOR ttTotais, ttSearch SCROLLING.

    DEFINE BROWSE bSource QUERY qSource DISPLAY
        ttSource.srcname         FORMAT "X(150)"               COLUMN-LABEL "Procedure" WIDTH 70
        ttSource.callcnt         FORMAT ">>>,>>>,>>9"          COLUMN-LABEL "Chamadas"
        ttSource.avg_acttime     FORMAT ">>>,>>>,>>9.999999"   COLUMN-LABEL "Tempo Medio"
        deTotalTime              FORMAT ">>>>>,>>>,>>9.999999" COLUMN-LABEL "Tempo Total"
        ttSource.session-percent FORMAT ">>>,>>9.999999"       COLUMN-LABEL "% Sessao"
        ttSource.tot_cumtime     FORMAT ">>>>>,>>>,>>9.999999" COLUMN-LABEL "Tempo Acum"
        WITH NO-ROW-MARKERS SEPARATORS SIZE 174 BY 8.00
            title "Procedures".

    DEFINE BROWSE bCaller QUERY qCaller DISPLAY
        bfTTCaller.srcname         FORMAT "X(150)"     COLUMN-LABEL "Quem executou" WIDTH 52
        bfTTCaller.callcnt         FORMAT ">,>>>,>>9"  COLUMN-LABEL "Qtd"
        bfTTCaller.session-percent FORMAT ">>9.999999" COLUMN-LABEL "% Sessao"
        WITH NO-ROW-MARKERS SEPARATORS SIZE 80 BY 9.00
            title "Quem Executou".

    DEFINE BROWSE bCallee QUERY qCallee DISPLAY
        bfTTCallee.srcname         FORMAT "X(150)"     COLUMN-LABEL "Progs Executados" WIDTH 52
        bfTTCallee.callcnt         FORMAT ">,>>>,>>9"  COLUMN-LABEL "Qtd"
        bfTTCallee.session-percent FORMAT ">>9.999999" COLUMN-LABEL "% Sessao"
        WITH NO-ROW-MARKERS SEPARATORS SIZE 93 BY 9.00
             TITLE "Programas executados".

    DEFINE BROWSE bLine QUERY qLine DISPLAY
        ttTotais.lineno       FORMAT ">>>,>>9"             COLUMN-LABEL "Linha"
        ttTotais.stmtcnt      FORMAT ">>>>>>,>>9"          COLUMN-LABEL "Qtd Exec"
        ttTotais.acttime      FORMAT ">>>,>>>,>>9.999999"  COLUMN-LABEL "Media Exec"
        ttTotais.tot_acttime  FORMAT  ">>>,>>>,>>9.999999" COLUMN-LABEL "Tempo Total"
        ttTotais.tot_cumtime  FORMAT ">>>,>>>,>>>9.999999" COLUMN-LABEL "Tempo Acumulado"
        ttSearch.IndexScore1  FORMAT "ZZ9.9%"              COLUMN-LABEL "Score#1"
        ttSearch.IndexScore2  FORMAT "ZZ9.9%"              COLUMN-LABEL "Score#2"
        ttSearch.DatabaseName FORMAT "X(12)"               COLUMN-LABEL "Banco de Dados"
        ttSearch.TableName    FORMAT "X(25)"               COLUMN-LABEL "Tabela"
        WITH NO-ROW-MARKERS SEPARATORS SIZE 174 BY 8.00
            title "Linhas".

    DEFINE FRAME f-log
        cbImport  AT ROW 01.50 COL 20 COLON-ALIGNED btProc LABEL "&Importar" SPACE(2)
        ttProfileSession.session-date LABEL "Data"
        ttProfileSession.session-time LABEL "Hora"
        ttProfileSession.tot_acttime  LABEL "Tempo Total Exec." FORMAT ">>>>,>>9.9999"
        SPACE(2)  btCompare
        SPACE(2)  btExit
        cFilter   AT ROW 02.50 COL 20 COLON-ALIGNED VIEW-AS FILL-IN SIZE 40 BY 1 LABEL "Localiza Procedure"
        btFilter  LABEL "&Buscar"
        bSource   AT ROW 03.50 COL 02
        bCaller   AT ROW 11.52 COL 02
        bCallee   AT ROW 11.52 COL 83
        bLine     AT ROW 20.63 COL 02
        WITH 1 DOWN NO-BOX KEEP-TAB-ORDER OVERLAY
             SIDE-LABELS NO-UNDERLINE THREE-D
             AT COL 1 ROW 3
             SIZE 178 BY 28.00.

    ON  CHOOSE OF btProc DO:
        DEFINE VARIABLE cArqImp    AS CHARACTER   NO-UNDO FORMAT "x(255)" LABEL "Arquivo"
                                      VIEW-AS EDITOR SIZE 80 BY 1.

        DEFINE BUTTON btImp     LABEL "&Importar" AUTO-GO.
        DEFINE BUTTON btCanc    LABEL "&Cancela"  AUTO-ENDKEY.

        PUBLISH "getPropParam" FROM THIS-PROCEDURE ("arquivoProgsProfiler", OUTPUT cArqImp).

        DEFINE FRAME f-imp
            cArqImp     AT ROW 01.5 COL 10 COLON-ALIGNED SPACE(0)
            btArq
            lStoreData  AT ROW 03.0 COL 10 COLON-ALIGNED
            btImp       AT ROW 05.0 COL 10 COLON-ALIGNED
            btCanc
            WITH SIDE-LABELS THREE-D SIZE 100 BY 7 DROP-TARGET
               VIEW-AS DIALOG-BOX TITLE "Arquivo do Profiler a Importar".

        ON  DROP-FILE-NOTIFY OF FRAME f-imp DO:
            DEFINE VARIABLE ix   AS INTEGER   NO-UNDO.
            DEFINE VARIABLE cTmp AS CHARACTER NO-UNDO.

            DO  ix = 1 TO FRAME f-imp:NUM-DROPPED-FILES:
                ASSIGN cTmp = FRAME f-imp:GET-DROPPED-FILE(ix).
                FILE-INFO:FILE-NAME = cTmp.
                IF  INDEX(FILE-INFO:FILE-TYPE, 'F') > 0  THEN DO:
                    cArqImp:screen-value = cTmp.
                    LEAVE.
                END.
            END.
            FRAME f-imp:END-FILE-DROP().
        END.

        ON  CHOOSE OF btArq DO:
            ASSIGN cArqImp.
            DEFINE VARIABLE lResp AS LOG NO-UNDO.
            SYSTEM-DIALOG GET-FILE cArqImp
                TITLE "Selecione o arquivo do profiler"
                FILTERS "*.out" "*.out",
                        "*.*" "*.*"
                MUST-EXIST
                INITIAL-DIR cArqImp
                USE-FILENAME
                UPDATE lResp.

            DISPLAY cArqImp WITH FRAME f-imp.
        END.

        ON  CHOOSE OF btImp DO:
            DEFINE VARIABLE c-formato AS CHARACTER NO-UNDO.
            DEFINE VARIABLE c-data    AS CHARACTER NO-UNDO.
            DEFINE VARIABLE iCont     AS INTEGER   NO-UNDO.

            ASSIGN cArqImp
                   lStoreData.
            FILE-INFO:FILE-NAME = cArqImp.
            IF  FILE-INFO:PATHNAME = ? THEN DO:
                MESSAGE "O arquivo do profiler " cArqImp "nao foi encontrado!"
                    VIEW-AS ALERT-BOX ERROR.
                RETURN NO-APPLY.
            END.

            PUBLISH "setPropParam" FROM THIS-PROCEDURE ("ArquivoProgsProfiler", cArqImp).
            PUBLISH "saveProp" FROM THIS-PROCEDURE.

            ASSIGN cArqImp  = REPLACE(cArqImp, "~\", "/")
                   cDir     = cArqImp
                   ENTRY(NUM-ENTRIES(cDir,"/"), cDir, "/") = ""
                   cArqImp  = ENTRY(NUM-ENTRIES(cArqImp, "/"), cArqImp, "/").

            SESSION:SET-WAIT-STATE("general").

            ASSIGN c-formato = SESSION:NUMERIC-FORMAT
                   c-data    = SESSION:DATE-FORMAT.

            SESSION:NUMERIC-FORMAT = "AMERICAN".
            SESSION:DATE-FORMAT    = "mdy".

            RUN leProfilerProf (cDir, cArqImp, lStoreData).

            SESSION:NUMERIC-FORMAT = c-formato.
            SESSION:DATE-FORMAT    = c-data.

            ASSIGN cLin  = "".
            FOR EACH ttProfileSession NO-LOCK:
                ASSIGN cLin  = cLin
                             + (IF cLin <> "" THEN "," ELSE "")
                             + String(ttProfileSession.session-id)
                             + ") "
                             + ttProfileSession.Session-Desc
                             + ","
                             + String(ttProfileSession.session-id)
                       iCont = iCont + 1.
            END.

            ASSIGN cbImport:LIST-ITEM-PAIRS IN FRAME f-log = cLin
                   cbImport:screen-value IN FRAME f-log    = ENTRY(2,cLin).

            SESSION:SET-WAIT-STATE("").

            APPLY "value-changed" TO cbImport IN FRAME f-log.

            HIDE MESSAGE NO-PAUSE.

            IF  iCont = 1 THEN
                PUBLISH "showMessage" FROM THIS-PROCEDURE ("Dica: Se voce realizar a importacao de outra sessao, poderas realizar a comparacao dos tempos de execucao das sessoes.").
            ELSE
                PUBLISH "showMessage" FROM THIS-PROCEDURE ("Dica: Se voce quiser, podes realizar a comparacao dos tempos de execucao das sessoes, clicando no botao 'Comparar'.").
        END.

        ON  RETURN OF cFilter DO:
            APPLY "CHOOSE" TO btFilter IN FRAME f-log.
        END.

        ON  GO OF FRAME f-imp DO:
            ASSIGN INPUT FRAME f-log cbImport.

            OPEN QUERY qSource FOR EACH ttSource
                WHERE ttSource.session-id = integer(cbImport)
                BY ttSource.session-id
                BY ttSource.tot_acttime DESCENDING
                BY ttSource.srcname.

            APPLY "value-changed" TO bSource IN FRAME f-log.

            ASSIGN btCompare:sensitive IN FRAME f-log = (NUM-ENTRIES(cbImport:LIST-ITEM-PAIRS) > 2).
        END.

        DISPLAY cArqImp lStoreData WITH FRAME f-imp.
        ENABLE ALL WITH FRAME f-imp.

        DO  ON  ENDKEY UNDO, LEAVE
            ON  ERROR UNDO, LEAVE:
            WAIT-FOR GO, ENDKEY OF FRAME f-imp.
        END.
    END.

    ON  ROW-DISPLAY OF bSource DO:
        deTotalTime = ttSource.avg_acttime * ttSource.callcnt.
    END.

    ON  VALUE-CHANGED OF cbImport DO:
        ASSIGN cbImport.
        FIND FIRST ttProfileSession
            WHERE ttProfileSession.session-id = integer(cbImport)
            NO-LOCK NO-ERROR.
        IF  AVAILABLE ttProfileSession THEN DO:
            DISPLAY ttProfileSession.session-date
                 ttProfileSession.session-time
                 ttProfileSession.tot_acttime
                 WITH FRAME f-log.
        END.

        OPEN QUERY qSource FOR EACH ttSource
            WHERE ttSource.session-id = integer(cbImport)
            BY ttSource.session-id
            BY ttSource.tot_acttime DESCENDING
            BY ttSource.srcname.

        APPLY "value-changed" TO bSource.
    END.

    ON  MOUSE-SELECT-DBLCLICK OF bCallee DO:
        RUN changeSourceProf (INPUT bfTTCallee.srcid, bSource:handle, bLine:handle).
    END.

    ON  MOUSE-SELECT-DBLCLICK OF bCaller DO:
        RUN changeSourceProf (INPUT bfTTCaller.srcid, bSource:handle, bLine:handle).
    END.

    ON  MOUSE-SELECT-CLICK OF bSource DO:
        IF  AVAILABLE ttSource
        AND bSource:CURRENT-COLUMN <> ? THEN DO:
            APPLY "recall" TO FRAME f-log.
        END.
    END.

    ON  RECALL OF FRAME f-log DO:
        IF  AVAILABLE ttSource
        AND bSource:CURRENT-COLUMN <> ? THEN DO:
            IF  bSource:CURRENT-COLUMN = bSource:GET-BROWSE-COLUMN(1) THEN
                OPEN QUERY qSource FOR EACH ttSource
                    WHERE ttSource.session-id = integer(cbImport)
                    BY ttSource.session-id
                    BY ttSource.srcname.
            ELSE IF  bSource:CURRENT-COLUMN = bSource:GET-BROWSE-COLUMN(2) THEN
                OPEN QUERY qSource FOR EACH ttSource
                    WHERE ttSource.session-id = integer(cbImport)
                    BY ttSource.session-id
                    BY ttSource.callcnt DESCENDING
                    BY ttSource.srcname.
            ELSE IF  bSource:CURRENT-COLUMN = bSource:GET-BROWSE-COLUMN(3) THEN
                OPEN QUERY qSource FOR EACH ttSource
                    WHERE ttSource.session-id = integer(cbImport)
                    BY ttSource.session-id
                    BY ttSource.avg_acttime DESCENDING
                    BY ttSource.srcname.
            ELSE IF bSource:CURRENT-COLUMN = bSource:GET-BROWSE-COLUMN(4) THEN
                OPEN QUERY qSource FOR EACH ttSource
                    WHERE ttSource.session-id = integer(cbImport)
                    BY ttSource.session-id
                    BY ttSource.tot_acttime DESCENDING
                    BY ttSource.srcname.
            ELSE IF bSource:CURRENT-COLUMN = bSource:GET-BROWSE-COLUMN(5) THEN
                OPEN QUERY qSource FOR EACH ttSource
                    WHERE ttSource.session-id = integer(cbImport)
                    BY ttSource.session-id
                    BY ttSource.session-percent DESCENDING
                    BY ttSource.srcname.
            ELSE IF bSource:CURRENT-COLUMN = bSource:GET-BROWSE-COLUMN(6) THEN
                OPEN QUERY qSource FOR EACH ttSource
                    WHERE ttSource.session-id = integer(cbImport)
                    BY ttSource.session-id
                    BY ttSource.tot_cumtime DESCENDING
                    BY ttSource.srcname.
        END.
    END.

    ON  VALUE-CHANGED OF bSource DO:
        OPEN QUERY qCallee FOR EACH bfTTCallTree
            WHERE bfTTCallTree.session-id = ttSource.session-id
            AND   bfTTCallTree.caller = ttSource.srcid,
                EACH bfTTCallee
                    WHERE bfTTCallee.session-id = bfTTCallTree.session-id
                    AND   bfTTCallee.srcid      = bfTTCallTree.callee
                    BY bfTTCallee.session-percent DESCENDING.

        OPEN QUERY qCaller FOR EACH ttCallTree
            WHERE ttCallTree.session-id = ttSource.session-id
            AND   ttCallTree.callee     = ttSource.srcid,
                EACH bfTTCaller
                    WHERE bfTTCaller.session-id = ttCallTree.session-id
                    AND   bfTTCaller.srcid      = ttCallTree.caller
                    BY ttCallTree.callcnt DESCENDING.

        OPEN QUERY qLine FOR EACH ttTotais
            WHERE ttTotais.session-id = ttSource.session-id
            AND   ttTotais.srcid = ttSource.srcid,
                EACH ttSearch OUTER-JOIN
                    WHERE ttSearch.srcid  = ttTotais.srcid
                    AND   ttSearch.LineId = ttTotais.lineno
                    BY ttTotais.tot_acttime DESCENDING.

        RUN changeSourceProf (INPUT ttSource.srcId, bSource:handle, bLine:handle).
    END.

    ON  CHOOSE OF btFilter DO:
        ASSIGN cFilter
               cbImport.
        RUN exibeBuscaProf (cFilter, bSource:handle, bLine:handle, INTEGER(cbImport)).
    END.

    ON  CHOOSE OF btCompare DO:
        ASSIGN cbImport.
        RUN compareProf (cbImport).
    END.

    ENABLE ALL EXCEPT
        ttProfileSession.session-date
        ttProfileSession.session-time
        ttProfileSession.tot_acttime
        btCompare
        WITH FRAME f-log.

    ASSIGN bSource:ALLOW-COLUMN-SEARCHING IN FRAME f-log = TRUE
           bSource:COLUMN-RESIZABLE IN FRAME f-log       = TRUE.

    ASSIGN hFrame = FRAME f-log:Handle.

    HIDE MESSAGE NO-PAUSE.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Dica: Clique no botao 'Importar' para importar a sessao do profiler.").

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-log.
    END.

    HIDE MESSAGE NO-PAUSE.
    HIDE FRAME f-log NO-PAUSE.
END PROCEDURE.

PROCEDURE leProfilerProf:
    DEFINE INPUT PARAMETER pDir    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pAdd    AS LOGICAL   NO-UNDO.

    DEFINE VARIABLE hQuery AS HANDLE NO-UNDO.
    DEFINE VARIABLE hTmp   AS HANDLE NO-UNDO.

    IF  pAdd = FALSE THEN DO:
        EMPTY TEMP-TABLE ttSource.
        EMPTY TEMP-TABLE ttCallTree.
        EMPTY TEMP-TABLE ttTotais.
        EMPTY TEMP-TABLE ttProfileSession.
        EMPTY TEMP-TABLE ttCallTreedata.
    END.

    DO  ON ERROR UNDO, LEAVE
        ON QUIT UNDO, LEAVE
        ON STOP UNDO, LEAVE:
        RUN ImportDataProf (pDir, pArq) NO-ERROR.
    END.
END PROCEDURE.

PROCEDURE importTTCallTreeDataProf:
    DEFINE VARIABLE caller       AS INTEGER    NO-UNDO.
    DEFINE VARIABLE callerlineno AS INTEGER    NO-UNDO.
    DEFINE VARIABLE callee       AS INTEGER    NO-UNDO.
    DEFINE VARIABLE callcnt      AS INTEGER    NO-UNDO.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando dados (Call Tree)...").

    /* now read in all the calltree information */
    REPEAT ON ENDKEY UNDO, LEAVE:
        IMPORT caller callerlineno callee callcnt.

        CREATE ttCallTreedata.
        ASSIGN ttCallTreedata.session-id   = ttProfileSession.session-id
               ttCallTreedata.caller       = caller
               ttCallTreedata.callerlineno = callerlineno
               ttCallTreedata.callee       = callee
               ttCallTreedata.callcnt      = callcnt.
    END.

    MESSAGE "Gerando dados (Call Tree)...".

    FOR EACH ttCallTreedata OF ttProfileSession:
        FIND FIRST ttCallTree OF ttCallTreedata NO-ERROR.
        IF  NOT AVAILABLE ttCallTree THEN
            BUFFER-COPY ttCallTreedata TO ttCallTree.
        ELSE
            ttCallTree.callcnt = ttCallTree.callcnt + ttCallTreedata.callcnt.
    END.
END PROCEDURE.

PROCEDURE ImportDataProf:
    DEFINE INPUT PARAMETER pDir     AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq     AS CHARACTER NO-UNDO.

    DEFINE BUFFER bfParentSrc  FOR ttSource.
    DEFINE BUFFER bfLSource       FOR ttSource.

    DEFINE VARIABLE iSessionId AS INTEGER   NO-UNDO.
    DEFINE VARIABLE versno     AS INTEGER   NO-UNDO.
    DEFINE VARIABLE parentname AS CHARACTER NO-UNDO.
    DEFINE VARIABLE sname      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE sid        AS INTEGER   NO-UNDO.

    INPUT from value(cDir + pArq) NO-CONVERT.

    RUN importTTProfileSessionProf (OUTPUT iSessionId) NO-ERROR.

    FIND FIRST ttProfileSession
        WHERE ttProfileSession.session-id = iSessionId
        EXCLUSIVE-LOCK NO-ERROR.
    IF  NOT AVAILABLE ttProfileSession THEN DO:
        MESSAGE 'Nao ha sessao valida'
                VIEW-AS ALERT-BOX INFORMATION BUTTONS OK.
        RETURN.
    END.
    ASSIGN ttProfileSession.session-dir = pDir
           ttProfileSession.session-arq = pArq.

    RUN importTTSourceProf NO-ERROR.
    RUN importTTCallTreeDataProf NO-ERROR.
    RUN importTTTotaisProf NO-ERROR.

    IF  versno >= 1 THEN DO:
        /* for version 0, we didn't have this information */
        RUN importTraceInfoProf.

        PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando dados (Coverage)...").
        /* read coverage analysis information */
        coverblk:
        REPEAT:
            IMPORT sid sname ^.
            IF  sname <> "" THEN DO:
                /* we've got a procedure, function, or trigger -- find it's parent */
                FIND bfParentSrc
                    WHERE bfParentSrc.session-id = ttProfileSession.session-id
                    AND   bfParentSrc.srcid      = sid NO-ERROR.
                IF  NOT AVAILABLE bfParentSrc  THEN DO:
                    /*run skipcoverage. */
                    UNDO coverblk, NEXT coverblk.
                END.

                sname = bfParentSrc.srcname + " " + sname.

                FIND ttSource
                    WHERE ttSource.session-id = ttProfileSession.session-id
                    AND   ttSource.srcname    = sname NO-ERROR.
                IF  NOT AVAILABLE ttSource THEN DO:
                    /* this source was not executed during this profiling session */
                    FIND LAST bfLSource
                        WHERE bfLSource.session-id = ttProfileSession.session-id
                        NO-LOCK NO-ERROR.
                    CREATE ttSource.
                    ASSIGN ttSource.srcid      = bfLSource.srcid + 1
                           ttSource.session-id = bfLSource.session-id
                           ttSource.srcname    = sname.
                END.
                sid = ttSource.srcid.
            END.
            RUN importExecLinesProf.
        END.
        RUN importUserDataProf.
    END.
    INPUT close.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Calculando Estatisticas...").
    /* now massage the data */
    FOR EACH ttSource OF ttProfileSession:
        /* establish how many times this source was called */
        FOR EACH ttCallTree
            WHERE ttCallTree.session-id = ttProfileSession.session-id
            AND   ttCallTree.callee = ttSource.srcid:
            ttSource.callcnt = ttSource.callcnt + ttCallTree.callcnt.
        END.

        /* establish what the "parent" procedure is, if there is one */
         parentname = ENTRY(2, ttSource.srcname, " ") NO-ERROR.
         IF  NOT ERROR-STATUS:ERROR THEN DO:
             FIND FIRST bfParentSrc
                 WHERE bfParentSrc.session-id = ttProfileSession.session-id
                 AND   bfParentSrc.srcname = parentname NO-ERROR.
             IF  AVAILABLE bfParentSrc THEN
                 ASSIGN ttSource.parent = bfParentSrc.srcid
                        ttSource.listname = bfParentSrc.listname.
         END.

         /* compute the total actual time and average actual time for the procedure */
         FOR EACH ttTotais OF ttSource:
             ASSIGN ttSource.tot_acttime = ttSource.tot_acttime + ttTotais.tot_acttime
                    ttTotais.parent = IF ttSource.parent = 0 THEN ttSource.srcid ELSE ttSource.parent.
         END.
         IF  ttSource.callcnt > 0 THEN /* may be zero if only have coverage analysis
                                        * info on the source, but no execution during
                                        * this profiling session */
             ttSource.avg_acttime = ttSource.tot_acttime / ttSource.callcnt.
    END.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Calculando Percentuais de Execucao...").

    /* figure out the total session time so we can compute percentages */
    FIND ttTotais
        WHERE ttTotais.session-id = ttProfileSession.session-id
        AND ttTotais.srcid = 0
        AND ttTotais.lineno = 0 NO-ERROR.
    IF  NOT AVAILABLE(ttTotais) THEN
        FIND ttTotais
            WHERE ttTotais.session-id = ttProfileSession.session-id
            AND ttTotais.srcid = 1
            AND ttTotais.lineno = 0 NO-ERROR.
    IF  NOT AVAILABLE(ttTotais) THEN DO:
        MESSAGE "Nao foi possivel sumarizar os dados. Nao foi possivel encontrar informacoes necessarias."
                VIEW-AS ALERT-BOX.
        RETURN.
    END.

    ttProfileSession.tot_acttime = ttTotais.cumtime.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Calculando Percentuais das Procedures...").

    /* calculate runtime percentages */
    FOR EACH ttSource OF ttProfileSession:
        ASSIGN ttSource.session-percent = ttSource.tot_acttime * 100.0 / ttProfileSession.tot_acttime
               ttSource.percall-percent = ttSource.avg_acttime * 100.0 / ttProfileSession.tot_acttime.

        FOR EACH ttTotais OF ttSource:
            ASSIGN ttTotais.session-percent = ttTotais.acttime * 100.0 / ttProfileSession.tot_acttime.

            IF  ttSource.avg_acttime > 0 THEN
                ttTotais.perprocedure-percent = ttTotais.tot_acttime * 100.0 / ttSource.callcnt / ttSource.avg_acttime.
        END.
        FIND FIRST ttTotais
            WHERE ttTotais.session-id = ttSource.session-id
            AND ttTotais.srcid = ttSource.srcid
            AND ttTotais.lineno >= 0 NO-ERROR.
        IF  AVAILABLE ttTotais
        AND ttTotais.lineno = 0 THEN DO:
            ASSIGN ttSource.overhead_time  = ttTotais.acttime
                   ttSource.tot_cumtime    = ttTotais.tot_cumtime.
            FIND NEXT ttTotais
                WHERE ttTotais.session-id = ttSource.session-id
                AND ttTotais.srcid = ttSource.srcid
                AND ttTotais.lineno >= 0 NO-ERROR.
        END.
        IF  AVAILABLE ttTotais THEN
            ttSource.first-line = ttTotais.lineno.
        ELSE
            ttSource.first-line = 1.
        ttSource.Total-Time = ttSource.avg_acttime * ttSource.callcnt.
    END.
    /* calculate procedure exec times */
END PROCEDURE.

PROCEDURE importExecLinesProf:
    DEFINE VARIABLE line-no AS INTEGER    NO-UNDO.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando linhas de codigo executaveis...").

    /* now read in what executable lines there are for this source */
    REPEAT:
        IMPORT line-no.
    END.
END PROCEDURE.

PROCEDURE importTTProfileSessionProf:
    DEFINE OUTPUT PARAMETER iSessionId AS INTEGER NO-UNDO.

    DEFINE BUFFER bfSessionSrc FOR ttSource.

    DEFINE VARIABLE sesdate        AS DATE      NO-UNDO.
    DEFINE VARIABLE sesdesc        AS CHARACTER NO-UNDO.
    DEFINE VARIABLE sestime        AS CHARACTER NO-UNDO.
    DEFINE VARIABLE sesuser        AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iSession       AS INTEGER   NO-UNDO.
    DEFINE VARIABLE versno         AS INTEGER   NO-UNDO.
    DEFINE VARIABLE savedateformat AS CHARACTER NO-UNDO.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando dados (Profiler Session)...").

    ASSIGN savedateformat      = SESSION:DATE-FORMAT
           SESSION:DATE-FORMAT = "mdy".

    FOR LAST ttProfileSession BY session-id:
        ASSIGN iSession = ttProfileSession.session-id.
    END.
    ASSIGN iSession = iSession + 1.

    REPEAT ON ENDKEY UNDO, LEAVE:
        IMPORT versno sesdate sesdesc sestime sesuser.

        IF  versno <> 0
        AND versno <> 1
        AND versno <> 3 THEN DO:
            MESSAGE "Nao foi possivel exibir os dados. O programa nao tem como exibir os dados para a versao" versno
                    VIEW-AS ALERT-BOX.
            UNDO, RETURN.
        END.

        CREATE ttProfileSession.
        ASSIGN iSessionId                   = iSession
               ttProfileSession.session-id   = iSession
               session-notes                = "Importacao do Profiler"
               SESSION:DATE-FORMAT          = "mdy"
               ttProfileSession.session-date = sesdate
               ttProfileSession.Session-Desc = sesdesc
               ttProfileSession.Session-Time = sestime
               ttProfileSession.Session-User = sesuser
               SESSION:DATE-FORMAT          = savedateformat.

        CREATE bfSessionSrc. /* create source id 0 -- the session "source" */
        ASSIGN bfSessionSrc.session-id = ttProfileSession.session-id
               bfSessionSrc.srcid      = 0
               bfSessionSrc.srcname    = "Session"
               bfSessionSrc.callcnt    = 1
               bfSessionSrc.listname   = "" NO-ERROR.

        IF  ERROR-STATUS:ERROR THEN
            DELETE bfSessionSrc.
    END.
    ASSIGN SESSION:DATE-FORMAT = savedateformat.
END PROCEDURE.

PROCEDURE importTTSourceProf:
    DEFINE VARIABLE srcid    AS INTEGER    NO-UNDO.
    DEFINE VARIABLE srcname  AS CHARACTER  NO-UNDO.
    DEFINE VARIABLE listname AS CHARACTER  NO-UNDO.
    DEFINE VARIABLE crcval   AS INTEGER    NO-UNDO.

    DEFINE VARIABLE cextension AS CHARACTER  NO-UNDO.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando dados (Source)...").

    REPEAT ON ENDKEY UNDO, LEAVE:
        IMPORT srcid srcname listname crcval.

        IF  NOT CAN-FIND(FIRST ttSource
                           WHERE ttSource.session-id = ttProfileSession.session-id
                           AND   ttSource.srcid = srcid) THEN DO:
            CREATE ttSource.
            ASSIGN ttSource.session-id = ttProfileSession.session-id
                   ttSource.srcid      = srcid
                   ttSource.srcname    = srcname
                   ttSource.listname   = listname
                   ttSource.CRC-VAL    = crcval.
        END.

        IF  LENGTH(ttSource.srcname) > 2 THEN
            cExtension = SUBSTRING(ttSource.srcname, LENGTH(ttSource.srcname) - 1) NO-ERROR.

        IF  cExtension > "" AND INDEX(".w,.p", cExtension) > 0 THEN DO:
            IF  R-INDEX(ttSource.srcname, " ") > 0  THEN
                ttSource.srcfile = SUBSTRING(ttSource.srcname, R-INDEX(ttSource.srcname, " ") + 1).
            ELSE
                ttSource.srcfile = ttSource.srcname.
        END.
    END.
END PROCEDURE.

PROCEDURE importTTTotaisProf:
    DEFINE VARIABLE srcid       AS INTEGER    NO-UNDO.
    DEFINE VARIABLE lineno      AS INTEGER    NO-UNDO.
    DEFINE VARIABLE istmtcnt    AS INTEGER    NO-UNDO.
    DEFINE VARIABLE cumtime     AS DECIMAL    NO-UNDO.
    DEFINE VARIABLE stmtcnt     AS INTEGER    NO-UNDO.
    DEFINE VARIABLE tot_acttime AS DECIMAL    NO-UNDO.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando dados (Summary)...").

    /* now read in all the summary statements */
    REPEAT:
      IMPORT srcid lineno stmtcnt tot_acttime cumtime.

      CREATE ttTotais.
      ASSIGN ttTotais.session-id  = ttProfileSession.session-id
             ttTotais.srcid       = srcid
             ttTotais.lineno      = lineno
             ttTotais.stmtcnt     = stmtcnt
             ttTotais.tot_acttime = tot_acttime
             ttTotais.cumtime     = cumtime
             ttTotais.tot_cumtime = cumtime.

      ASSIGN ttTotais.acttime = ttTotais.tot_acttime / ttTotais.stmtcnt
             ttTotais.cumtime = ttTotais.cumtime / ttTotais.stmtcnt.
    END.
END PROCEDURE.

PROCEDURE importTraceInfoProf:
    DEFINE VARIABLE srcid     AS INTEGER    NO-UNDO.
    DEFINE VARIABLE line-no   AS INTEGER    NO-UNDO.
    DEFINE VARIABLE acttime   AS DECIMAL    NO-UNDO.
    DEFINE VARIABLE starttime AS DECIMAL    NO-UNDO.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando dados (Trace)...").

    /* read tracing information */
    REPEAT:
       IMPORT srcid line-no acttime starttime.
    END.
END PROCEDURE.

PROCEDURE importUserDataProf:
    DEFINE VARIABLE data       AS CHARACTER  NO-UNDO.
    DEFINE VARIABLE event-time AS DECIMAL    NO-UNDO.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando dados (User Data)...").

    /* read any user data */
    REPEAT:
        IMPORT event-time data.
    END.
END PROCEDURE.

PROCEDURE exibeBuscaProf:
    DEFINE INPUT PARAMETER cSearch   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER bSource   AS HANDLE    NO-UNDO.
    DEFINE INPUT PARAMETER bLine     AS HANDLE    NO-UNDO.
    DEFINE INPUT PARAMETER sessionId AS INTEGER   NO-UNDO.

    DEFINE BUFFER ttSourceAux   FOR ttSource.

    DEFINE VARIABLE qSource AS HANDLE    NO-UNDO.

    ASSIGN qSource = bSource:QUERY.

    DEFINE QUERY qrSourceAux FOR ttSourceAux SCROLLING.

    DEFINE BROWSE brSourceAux
      QUERY qrSourceAux NO-LOCK DISPLAY
          ttSourceAux.srcname FORMAT "X(150)"
          WITH NO-ROW-MARKERS EXPANDABLE SEPARATORS SIZE 100 BY 10 FONT 2.

    DEFINE BUTTON btBuscaOK AUTO-GO LABEL "&OK"     SIZE 10 BY 1.
    DEFINE BUTTON btCancel          LABEL "&Cancel" SIZE 10 BY 1.

    DEFINE FRAME f-search
        brSourceAux   AT ROW 1.50 COL 2
        btBuscaOK     AT ROW 12.50 COL 2.14
        btCancel      AT ROW 12.50 COL 13.14
        SPACE(0.28)
        WITH VIEW-AS DIALOG-BOX KEEP-TAB-ORDER SIDE-LABELS NO-UNDERLINE
             THREE-D SCROLLABLE TITLE "Registros Encontrados" FONT 1
             DEFAULT-BUTTON btBuscaOK.

    OPEN QUERY qrSourceAux
        FOR EACH ttSourceAux  NO-LOCK
            WHERE ttSourceAux.session-id = sessionId
            AND   ttSourceAux.srcname BEGINS cSearch.

    DISPLAY brSourceAux WITH FRAME f-search.

    ON  CHOOSE OF btCancel IN FRAME f-search DO:
        APPLY "GO":U TO FRAME f-search.
    END.

    ON  MOUSE-SELECT-DBLCLICK OF brSourceAux IN FRAME f-search
    OR  CHOOSE OF btBuscaOK IN FRAME f-search DO:
        qSource:reposition-TO-ROWID(ROWID(ttSourceAux)).
        RUN changeSourceProf (INPUT ttSource.srcId, bSource, bLine).
        APPLY "value-changed" TO bSource.
        APPLY "GO" TO FRAME f-search.
    END.

    ENABLE brSourceAux btBuscaOK btCancel WITH FRAME f-search.

    WAIT-FOR "GO" OF FRAME f-search.
END PROCEDURE.

PROCEDURE changeSourceProf:
    DEFINE INPUT  PARAMETER pSrcId  AS INTEGER  NO-UNDO.
    DEFINE INPUT  PARAMETER bSource AS HANDLE   NO-UNDO.
    DEFINE INPUT  PARAMETER bLine   AS HANDLE   NO-UNDO.

    DEFINE VARIABLE cFile    AS CHARACTER  NO-UNDO.
    DEFINE VARIABLE hqsource AS HANDLE     NO-UNDO.
    DEFINE VARIABLE iSrcId   AS INTEGER    NO-UNDO.

    DEFINE BUFFER bfTTSource FOR ttSource.

    SESSION:SET-WAIT-STATE("general":u).

    IF  pSrcId <> ttSource.srcid THEN DO:
        FIND FIRST bfTTSource
            WHERE bfTTSource.srcid = pSrcid
            NO-LOCK NO-ERROR.
        IF  AVAILABLE bfTTSource THEN DO:
            hqsource = bSource:QUERY.
            hqsource:REPOSITION-TO-ROWID (ROWID(bfTTSource)).
            APPLY "value-changed" TO bSource.
        END.
    END.
    APPLY "value-changed" TO bLine.

    SESSION:SET-WAIT-STATE("":u).
END PROCEDURE.

PROCEDURE compareProf:
    DEFINE INPUT PARAMETER sessionId AS CHARACTER NO-UNDO.

    DEFINE VARIABLE ttComp     AS HANDLE     NO-UNDO.
    DEFINE VARIABLE bComp      AS HANDLE     NO-UNDO.
    DEFINE VARIABLE qComp      AS HANDLE     NO-UNDO.
    DEFINE VARIABLE iCount     AS INTEGER    NO-UNDO.
    DEFINE VARIABLE hCol       AS HANDLE     NO-UNDO.
    DEFINE VARIABLE bfComp     AS HANDLE     NO-UNDO.
    DEFINE VARIABLE cLin       AS CHARACTER  NO-UNDO.
    DEFINE VARIABLE cSess      AS CHARACTER  NO-UNDO.
    DEFINE VARIABLE lOrdem     AS LOGICAL    NO-UNDO INITIAL TRUE.

    DEFINE BUFFER b1ttSource FOR ttSource.
    DEFINE BUFFER b2ttSource FOR ttSource.

    DEFINE VARIABLE cbSess1 AS CHARACTER FORMAT "X(90)":U NO-UNDO
                               VIEW-AS COMBO-BOX INNER-LINES 5 DROP-DOWN-LIST SIZE 41 BY 1.

    DEFINE VARIABLE cbSess2 AS CHARACTER FORMAT "X(90)":U NO-UNDO
                               VIEW-AS COMBO-BOX INNER-LINES 5 DROP-DOWN-LIST SIZE 39 BY 1.

    DEFINE VARIABLE cDetail AS CHARACTER   NO-UNDO FORMAT "x(255)" LABEL "Procedure"
                               VIEW-AS EDITOR SIZE 100 BY 1.

    DEFINE FRAME f-comp
        cbSess1            AT ROW 1.25 COL 2 NO-LABELS
        "<-- Comparar -->" AT ROW 1.35 COL 45
        cbSess2            AT ROW 1.25 COL 60 COLON-ALIGNED NO-LABELS SPACE(10)
        btPrint            SPACE(5)
        btExit
        cDetail            AT ROW 26 COL 2
        WITH 1 DOWN KEEP-TAB-ORDER OVERLAY
             SIDE-LABELS NO-UNDERLINE THREE-D
             SIZE 186 BY 28
             VIEW-AS DIALOG-BOX TITLE "Comparacao de Sessoes".

    /* cria a temp-table de resultados */
    CREATE TEMP-TABLE ttComp.
    ttComp:ADD-NEW-FIELD("source_name", "character", 1, "X(150)", "", "Procedure").
    ttComp:ADD-NEW-FIELD("callsto1", "integer", 1, ">>>>,>>9.99", 0, "", "Qtd!Exec 1").
    ttComp:ADD-NEW-FIELD("callsto2", "integer", 1, ">>>>,>>9.99", 0, "", "Qtd!Exec 2").
    ttComp:ADD-NEW-FIELD("avg1", "decimal", 1, ">>9.999999", 0, "", "Media!Tempo 1").
    ttComp:ADD-NEW-FIELD("avg2", "decimal", 1, ">>9.999999", 0, "", "Media!Tempo 2").
    ttComp:ADD-NEW-FIELD("Tot1", "decimal", 1, ">,>>9.999999", 0, "", "Tempo!Total 1").
    ttComp:ADD-NEW-FIELD("Tot2", "decimal", 1, ">,>>9.999999", 0, "", "Tempo!Total 2").
    ttComp:ADD-NEW-FIELD("percent1", "decimal", 1, ">>9.999999", 0, "Sess % 1").
    ttComp:ADD-NEW-FIELD("percent2", "decimal", 1, ">>9.999999", 0, "Sess % 2").
    ttComp:ADD-NEW-FIELD("cum1", "decimal", 1, ">>>>,>>>9.999999", 0, "", "Tempo!Acum 1").
    ttComp:ADD-NEW-FIELD("cum2", "decimal", 1, ">>>>,>>>9.999999", 0, "", "Tempo!Acum 2").
    ttComp:ADD-NEW-INDEX("iname").
    ttComp:ADD-INDEX-FIELD("iname", "source_name").
    ttComp:TEMP-TABLE-PREPARE("ttResult").

    /* cria a query */
    CREATE QUERY qComp.
    bfComp = ttComp:DEFAULT-BUFFER-HANDLE.
    qComp:SET-BUFFERS(bfComp).

    /* cria o browse */
    CREATE BROWSE bComp
        ASSIGN
           COL                    = 2
           ROW                    = cbSess1:HEIGHT + 1.3
           WIDTH                  = 182
           HEIGHT                 = 23.5
           ALLOW-COLUMN-SEARCHING = TRUE
           COLUMN-MOVABLE         = FALSE
           COLUMN-RESIZABLE       = TRUE
           COLUMN-SCROLLING       = TRUE
           FRAME                  = FRAME f-comp:HANDLE
           READ-ONLY              = TRUE
           ROW-MARKERS            = FALSE
           SEPARATORS             = TRUE
           QUERY                  = qComp.

    DO  iCount = 1 TO ttComp:DEFAULT-BUFFER-HANDLE:NUM-FIELDS:
        bComp:ADD-LIKE-COLUMN(ttComp:DEFAULT-BUFFER-HANDLE:BUFFER-FIELD(iCount)).
    END.

    hCol = bComp:GET-BROWSE-COLUMN(1).
    hCol:WIDTH = 36.
    hCol = bComp:GET-BROWSE-COLUMN(3).
    hCol:COLUMN-FGCOLOR = 1.
    hCol = bComp:GET-BROWSE-COLUMN(5).
    hCol:COLUMN-FGCOLOR = 1.
    hCol = bComp:GET-BROWSE-COLUMN(7).
    hCol:COLUMN-FGCOLOR = 1.
    hCol = bComp:GET-BROWSE-COLUMN(9).
    hCol:COLUMN-FGCOLOR = 1.
    hCol = bComp:GET-BROWSE-COLUMN(11).
    hCol:COLUMN-FGCOLOR = 1.

    ON  VALUE-CHANGED OF cbSess1, cbSess2 IN FRAME f-comp DO:
        ASSIGN cbSess1
               cbSess2.

        DEFINE VARIABLE lOk        AS LOGICAL    NO-UNDO.

        qComp:QUERY-CLOSE().

        bfComp:EMPTY-TEMP-TABLE().

        FIND FIRST b1ttSource
            WHERE b1ttSource.session-id = INTEGER(cbSess1)
            NO-LOCK NO-ERROR.
        FIND FIRST b2ttSource
            WHERE b2ttSource.session-id = INTEGER(cbSess2)
            NO-LOCK NO-ERROR.

        IF  NOT AVAILABLE b1ttSource
        OR  NOT AVAILABLE b2ttSource THEN
            RETURN.

        SESSION:SET-WAIT-STATE("GENERAL":U).
        FOR EACH b1ttSource
            WHERE b1ttSource.session-id = INTEGER(cbSess1):
            lOk = bfComp:FIND-FIRST("where source_name = ~"" + b1ttSource.srcname + "~"") NO-ERROR.
            IF  NOT lOk THEN
                bfComp:BUFFER-CREATE().
            ASSIGN bfComp:BUFFER-FIELD("source_name":U):BUFFER-VALUE  = b1ttSource.srcname
                   bfComp:BUFFER-FIELD("callsto1":U):BUFFER-VALUE     = b1ttSource.callcnt
                   bfComp:BUFFER-FIELD("avg1":U):BUFFER-VALUE         = b1ttSource.avg_acttime
                   bfComp:BUFFER-FIELD("tot1":U):BUFFER-VALUE         = b1ttSource.total-time
                   bfComp:BUFFER-FIELD("percent1":U):BUFFER-VALUE     = b1ttSource.session-percent
                   bfComp:BUFFER-FIELD("cum1":U):BUFFER-VALUE         = b1ttSource.tot_cumtime.
        END.

        FOR EACH b2ttSource
            WHERE b2ttSource.session-id = INTEGER(cbSess2):
            lOk = bfComp:FIND-FIRST("where source_name = ~"" + b2ttSource.srcname + "~"") NO-ERROR.
            IF  NOT lOk THEN
                bfComp:BUFFER-CREATE().
            ASSIGN bfComp:BUFFER-FIELD("source_name":U):BUFFER-VALUE  = b2ttSource.srcname
                   bfComp:BUFFER-FIELD("callsto2":U):BUFFER-VALUE     = b2ttSource.callcnt
                   bfComp:BUFFER-FIELD("avg2":U):BUFFER-VALUE         = b2ttSource.avg_acttime
                   bfComp:BUFFER-FIELD("tot2":U):BUFFER-VALUE         = b2ttSource.total-time
                   bfComp:BUFFER-FIELD("percent2":U):BUFFER-VALUE     = b2ttSource.session-percent
                   bfComp:BUFFER-FIELD("cum2":U):BUFFER-VALUE         = b2ttSource.tot_cumtime.
        END.

        ASSIGN bComp:SENSITIVE = TRUE
               bComp:VISIBLE   = TRUE.
        SESSION:SET-WAIT-STATE("":U).

        APPLY "recall" TO FRAME f-comp.
        APPLY "value-changed" TO bComp.
    END.

    ON  VALUE-CHANGED OF bComp DO:
        IF  bfComp:available THEN
            ASSIGN cDetail:screen-value IN FRAME f-comp = bfComp:BUFFER-FIELD("source_name":U):BUFFER-VALUE.
        ELSE
            ASSIGN cDetail:screen-value IN FRAME f-comp = "".
    END.

    ON  MOUSE-SELECT-CLICK OF bComp DO:
        IF  bfComp:AVAILABLE
        AND bComp:CURRENT-COLUMN <> ? THEN
            APPLY "recall" TO FRAME f-comp.
    END.

    ON  RECALL OF FRAME f-comp DO:
        DEFINE VARIABLE cQuery AS CHARACTER NO-UNDO.

        ASSIGN cQuery = "for each ttResult ".

        IF  bfComp:AVAILABLE
        AND bComp:current-column <> ? THEN
            ASSIGN cQuery = cQuery
                          + " by ttResult." + bComp:current-column:name
                          + (IF lOrdem THEN " desc" ELSE "")
                   lOrdem = NOT lOrdem.
       ELSE
            ASSIGN cQuery = cQuery
                          + " by ttResult.source_name".

        qComp:QUERY-CLOSE().

        qComp:QUERY-PREPARE(cQuery).

        qComp:QUERY-OPEN().

        APPLY "VALUE-CHANGED" TO bComp.
        APPLY "entry" TO bComp.
    END.

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.
        DEFINE VARIABLE hField    AS HANDLE    NO-UNDO.
        ASSIGN cbSess1
               cbSess2.
        DEFINE BUFFER bfProf FOR ttProfileSession.
        FIND FIRST bfProf
            WHERE bfProf.session-id = integer(cbSess1)
            NO-LOCK NO-ERROR.
        ASSIGN cArqPrint = bfProf.session-dir + "/"
                         + ENTRY(1, bfProf.session-arq, ".") + "_compare_"
                         + cbSess1 + "_com_" + cbSess2 + ".log".
        OUTPUT TO VALUE(cArqPrint).
        /* export column headers */
        DO  iCount = 1 TO bfComp:NUM-FIELDS:
            hfield = bfComp:BUFFER-FIELD(icount).
            PUT UNFORMATTED hField:NAME ";".
        END.

        PUT UNFORMATTED SKIP.
        qComp:GET-FIRST().
        DO  WHILE NOT qComp:QUERY-OFF-END:
            DO  iCount = 1 TO bfComp:NUM-FIELDS:
                hfield = bfComp:BUFFER-FIELD(icount).
                PUT UNFORMATTED hField:BUFFER-VALUE ";".
            END.
            PUT UNFORMATTED SKIP.

            qComp:GET-NEXT().
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ASSIGN cDetail:read-only = TRUE.

    ENABLE ALL WITH FRAME f-comp.

    ASSIGN cLin  = ""
           cSess = "".
    FOR EACH ttProfileSession NO-LOCK:
        IF  STRING(ttProfileSession.session-id) <> sessionId
        AND cSess = "" THEN
            ASSIGN cSess = STRING(ttProfileSession.session-id).
        ASSIGN cLin = cLin
                    + (IF cLin <> "" THEN "," ELSE "")
                    + String(ttProfileSession.session-id)
                    + ") "
                    + ttProfileSession.Session-Desc
                    + ","
                    + String(ttProfileSession.session-id).
    END.

    ASSIGN cbSess1:LIST-ITEM-PAIRS = cLin
           cbSess1:screen-value    = sessionId
           cbSess2:LIST-ITEM-PAIRS = cLin
           cbSess2:screen-value    = cSess.

    APPLY "value-changed" TO cbSess2.

    DO  ON  ENDKEY UNDO, LEAVE
        ON  ERROR UNDO, LEAVE:
        WAIT-FOR GO, ENDKEY OF FRAME f-comp.
    END.
    FINALLY:
        qComp:QUERY-CLOSE().
        bfComp:EMPTY-TEMP-TABLE().
        DELETE OBJECT ttComp NO-ERROR.
        DELETE OBJECT bComp  NO-ERROR.
        DELETE OBJECT qComp  NO-ERROR.
        DELETE OBJECT hCol   NO-ERROR.
    END.
END PROCEDURE.

/* fim */
