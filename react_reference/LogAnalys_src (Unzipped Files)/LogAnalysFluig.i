/************************************************************************************************
** Procedures para JBOSS FLUIG
************************************************************************************************/

PROCEDURE criaTTFluig:
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
    ttLog:ADD-NEW-FIELD("tcLinh", "CHAR",0,"x(125)","","Conteudo").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcType").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc", "tcType").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcData").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcHora").
    ttLog:ADD-INDEX-FIELD("dataProc", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hBuffer = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logFluig:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cChave    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBrowse   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBuffer   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hTTLog    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE lOrdem    AS LOGICAL   NO-UNDO INITIAL TRUE.
    DEFINE VARIABLE lUseDate  AS LOGICAL   NO-UNDO.

    DEFINE QUERY qDetail FOR ttDetail.

    DEFINE BROWSE bDetail QUERY qDetail DISPLAY
        ttDetail.tiSeq
        WITH 7 DOWN size 15 by 8.

    DEFINE FRAME f-log
        cbTypeLst  AT ROW 01.5 COL 3
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
    RUN criaTTFluig (OUTPUT hTTLog, OUTPUT hBuffer).

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

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        ASSIGN cbTypeLst.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + ".log".
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

        ASSIGN cbTypeLst.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + cbTypeLst + "_tmp.log".
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

        ASSIGN cbTypeLst.

        ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcType = '" + cbTypeLst + "'"
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
        APPLY "value-changed" TO cbTypeLst.
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

        APPLY "value-changed" TO cbTypeLst.
    END.

    ASSIGN cDados:READ-ONLY = TRUE
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse
           hDet             = BROWSE bDetail:handle.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaFluig (pDir, pArq, hBuffer).

    ASSIGN lUseDate = (RETURN-VALUE = "yes").

    /* adiciona as colunas do browse */
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiLinh")).
    IF  lUseDate = TRUE THEN
        hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcData")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHora")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcLinh")).

    ASSIGN cbTypeLst:LIST-ITEMS = getListType().
    IF  CAN-DO(cbTypeLst:LIST-ITEMS, "ERROR") THEN
        ASSIGN cbTypeLst:SCREEN-VALUE = "ERROR".
    ELSE
        ASSIGN cbTypeLst:SCREEN-VALUE = ENTRY(1,cbTypeLst:LIST-ITEMS).

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    APPLY "value-changed" TO cbTypeLst.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.

    ASSIGN dDatIni:sensitive = lUseDate
           dDatFim:sensitive = lUseDate.

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

PROCEDURE importaFluig:
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

    RUN processaFluig (hBuffer).

    HIDE MESSAGE NO-PAUSE.

    RETURN RETURN-VALUE.
END PROCEDURE.

PROCEDURE processaFluig:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE iLinTot   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE lUseDate  AS LOGICAL   NO-UNDO.
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

        IF  TRIM(cLin) BEGINS cAno  + "-" 
        OR  TRIM(cLin) BEGINS cAnoA + "-" THEN
            ASSIGN lUseDate = TRUE.

        IF  INDEX(cLin, " ERROR [")  > 0
        OR  INDEX(cLin, " SEVERE [") > 0
        OR  INDEX(cLin, " WARN  [")  > 0 THEN DO:
            IF  INDEX(cLin, "log4j:") = 0 THEN DO:
                ASSIGN cLin2 = cLin
                       ix    = 1.
                FOR EACH bfLin EXCLUSIVE-LOCK
                    WHERE bfLin.tiLinh > ttLin.tiLinh:
                    ASSIGN cLin3 = bfLin.tcLinh.

                    IF  TRIM(cLin3) = "" THEN DO:
                        DELETE bfLin.
                        NEXT.
                    END.

                    IF  TRIM(cLin3) BEGINS cAno  + "-"
                    OR  TRIM(cLin3) BEGINS cAnoA + "-" THEN
                        ASSIGN lUseDate = TRUE.

                    IF  (INDEX(cLin3, " ERROR [") > 0
                    OR   INDEX(cLin3, " SEVERE [") > 0)
                    AND (lUseDate = TRUE
                    OR  (substr(cLin, 3, 1) = ":"
                    AND  substr(cLin, 6, 1) = ":")) THEN DO:
                        IF  LENGTH(cLin2) > 15000 THEN DO:
                            createTTDetail (cLin2, ttLin.tiLinh, ix).
                            ASSIGN ix    = ix + 1
                                   cLin2 = "".
                        END.
                        ASSIGN cLin3 = REPLACE(cLin3, "ERROR [", "[")
                               cLin2 = cLin2
                                     + (IF  cLin2 <> "" THEN CHR(10) ELSE "")
                                     + cLin3.
                        DELETE bfLin.
                        NEXT.
                    END.

                    IF  TRIM(cLin3) BEGINS cAno  + "-"
                    OR  TRIM(cLin3) BEGINS cAnoA + "-"
                    OR  NUM-ENTRIES(ENTRY(1, cLin3, " "),":") > 2 THEN
                        LEAVE.

                    IF  LENGTH(cLin2) > 15000 THEN DO:
                        createTTDetail (cLin2, ttLin.tiLinh, ix).
                        ASSIGN ix    = ix + 1
                               cLin2 = "".
                    END.
                    ASSIGN cLin2 = cLin2
                                 + (IF  cLin2 <> "" THEN CHR(10) ELSE "")
                                 + cLin3.
                    DELETE bfLin.
                END.
                IF  LENGTH(cLin2) > 0 THEN DO:
                    createTTDetail (cLin2, ttLin.tiLinh, ix).
                    ASSIGN ix    = ix + 1
                           cLin2 = "".
                END.
                RUN criaLinFluig ("ERROR", ttLin.tcLinh, "", ttLin.tiLinh, hBuffer).
            END.
            DELETE ttLin.
            NEXT.
        END.

        ASSIGN cLin = TRIM(cLin).

        IF  INDEX(cLin, "INFO  [STDOUT]") > 0
        AND TRIM(ENTRY(2, cLin, "]")) = ""  THEN DO:
            DELETE ttLin.
            NEXT.
        END.

        RUN criaLinFluig ("", cLin, cLin, ttLin.tiLinh, hBuffer).
        createTTDetail (ttLin.tcLinh, ttLin.tiLinh, 1).
    END.
    RETURN STRING(lUseDate).
END PROCEDURE.

PROCEDURE criaLinFluig:
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

    ASSIGN cLin  = REPLACE(cLin, "[STDERR] ", "").

    IF  (substr(cLin, 3, 1) = ":"
    AND  substr(cLin, 6, 1) = ":") THEN
         ASSIGN cHora               = ENTRY(1, cLin, " ")
                ENTRY(1, cLin, " ") = ""
                cLin                = TRIM(cLin)
                cData               = ""
                dData               = TODAY.

    IF  TRIM(cLin) BEGINS cAno + "-" 
    OR  TRIM(cLin) BEGINS cAnoA + "-" THEN
        ASSIGN cData               = ENTRY(1, cLin, " ")
               cHora               = ENTRY(2, cLin, " ")
               ENTRY(1, cLin, " ") = ""
               ENTRY(2, cLin, " ") = ""
               cLin                = TRIM(cLin).

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
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()  = cTxt NO-ERROR.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() = iLin.

    RUN criaCateg (cType, "").
END PROCEDURE.

/* fim */
