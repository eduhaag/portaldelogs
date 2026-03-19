/************************************************************************************************
** Procedures para Appserver Performance
************************************************************************************************/

PROCEDURE criaTTAppPerf:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hLogBuf AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLog:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh",  "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcHoraI", "CHAR",0,"X(13)","","HoraI","Hora!Inicial").
    ttLog:ADD-NEW-FIELD("tcHoraF", "CHAR",0,"X(13)","","HoraF","Hora!Final").
    ttLog:ADD-NEW-FIELD("tiHoraD", "INTE",0,"","","Duracao Ms", "Duracao!Milis").
    ttLog:ADD-NEW-FIELD("tcTxt",   "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcLinh",  "CHAR",0,"x(100)","","Conteudo").
    ttLog:ADD-NEW-FIELD("tcProc",  "CHAR",0,"x(20)","","Processo").
    ttLog:ADD-NEW-FIELD("tcProg",  "CHAR",0,"x(15)","","Programa").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcProc").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc", "tiHoraD", "descending").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcProc").
    ttLog:ADD-INDEX-FIELD("dataProc", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hLogBuf = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logAppPerf:
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
        cbFilter   AT ROW 02.50 COL 3
        cFilter    VIEW-AS FILL-IN SIZE 70 BY 1 NO-LABELS
        btFilter   btClear
        bDetail    AT ROW 19.5 COL 3
        cDados     NO-LABELS AT ROW 19.5 COL 18
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTAppPerf (OUTPUT hTTLog, OUTPUT hBuffer).

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
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiHoraD")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHoraI")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHoraF")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcProc")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcLinh")).

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_tempo" + ".log".
        OUTPUT TO VALUE(cArqPrint).
        PUT UNFORMATTED
            "Duracao;Hora Inicial;Hora Final;Processo;Conteudo"
            SKIP.
        hQuery:GET-FIRST().
        DO  WHILE NOT hQuery:QUERY-OFF-END:
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tiHoraD"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcHoraI"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcHoraF"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE()  ";"
                hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE()
                SKIP.
            hQuery:GET-NEXT().
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  CHOOSE OF btClip IN FRAME f-log DO:
        DEFINE VARIABLE cLin AS CHARACTER NO-UNDO.
        IF  hBuffer:AVAILABLE THEN DO:
            ASSIGN cLin = "Duracao.....: " + String(hBuffer:BUFFER-FIELD("tiHoraD"):BUFFER-VALUE()) + chr(10)
                        + "Hora Inicial: " + hBuffer:BUFFER-FIELD("tcHoraI"):BUFFER-VALUE() + chr(10)
                        + "Hora Final..: " + hBuffer:BUFFER-FIELD("tcHoraF"):BUFFER-VALUE() + chr(10)
                        + "Processo....: " + hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE()  + chr(10)
                        + "Conteudo....: " + hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE()  + chr(10).
            ASSIGN CLIPBOARD:VALUE = cLin.
        END.
    END.

    ON  CHOOSE OF btNotepad IN FRAME f-log DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        DEFINE BUFFER bfDet FOR ttDetail.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_tmp.log".
        OUTPUT TO VALUE(cArqPrint).
        PUT UNFORMATTED 
            "Duracao.....: " + String(hBuffer:BUFFER-FIELD("tiHoraD"):BUFFER-VALUE()) + chr(10)
            "Hora Inicial: " + hBuffer:BUFFER-FIELD("tcHoraI"):BUFFER-VALUE() + chr(10)
            "Hora Final..: " + hBuffer:BUFFER-FIELD("tcHoraF"):BUFFER-VALUE() + chr(10)
            "Processo....: " + hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE()  + chr(10)
            "Conteudo....: " + hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE()  + chr(10)
            SKIP.
        
        FOR EACH bfDet NO-LOCK
            WHERE bfDet.tiLinh = hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE():
            PUT UNFORMATTED
                bfDet.tcLinh SKIP.
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  MOUSE-SELECT-CLICK OF hBrowse DO:
        IF  hBuffer:AVAILABLE
        AND hBrowse:CURRENT-COLUMN <> ? THEN DO:
            ASSIGN lOrdem = TRUE.
            APPLY "choose" TO btFilter IN FRAME f-log.
        END.
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
        ASSIGN cFilter:SCREEN-VALUE = "".
        APPLY "choose" TO btFilter.
    END.

    ON  CHOOSE OF btFilter
    OR  RETURN OF cFilter DO:
        DEFINE VARIABLE cQuery AS CHARACTER NO-UNDO.

        ASSIGN cbFilter
               cFilter.

        ASSIGN cChave = "".

        IF  cFilter <> "" THEN DO:
            CASE cbFilter:
                WHEN "Processo" THEN ASSIGN cChave = " where ttLog.tcProg matches '*" + cFilter + "*'".
                WHEN "Conteudo" THEN ASSIGN cChave = " where ttLog.tcLinh matches '*" + cFilter + "*'".
            END CASE.
        END.

        ASSIGN cQuery = "FOR EACH ttLog"
                      + cChave.

        IF  hBuffer:AVAILABLE
        AND hBrowse:current-column <> ? THEN
            ASSIGN cQuery = cQuery
                          + " by ttLog." + hBrowse:current-column:name
                          + (IF lOrdem THEN " desc" ELSE "")
                   lOrdem = NOT lOrdem.
       ELSE
            ASSIGN cQuery = cQuery
                          + " BY ttLog.tiHoraD descending".

        hQuery:QUERY-CLOSE().

        hQuery:QUERY-PREPARE(cQuery).

        hQuery:QUERY-OPEN().

        APPLY "VALUE-CHANGED" TO hBrowse.
        APPLY "entry" TO hBrowse.
    END.

    ASSIGN cDados:READ-ONLY = TRUE
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse
           hDet             = BROWSE bDetail:handle.

    ASSIGN cbFilter:list-items = "Processo,Conteudo".

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaAppPerf (pDir, pArq, hBuffer).

    APPLY "choose" TO btFilter.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.

    IF  NOT hBuffer:AVAILABLE THEN DO:
        MESSAGE "Aparentemente nao consegui detectar nenhuma tag para monitorar a performance." SKIP
                "Favor verificar se a configuracao do log do Appserver esta incluida a tag 'ASPlumbing' no LogEntryTypes."
                VIEW-AS ALERT-BOX WARNING.
    END.

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

PROCEDURE importaAppPerf:
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

        IF  NOT cLin BEGINS "["
        OR  NUM-ENTRIES(cLin, " ") < 3 THEN
            NEXT.

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.

        CREATE ttLin.
        ASSIGN ttLin.tcLinh = cLin
               ttLin.tiLinh = iLinOrg
               ttLin.tcProc = ENTRY(2, cLin, " ") + " " + entry(3, cLin, " ")
               ttLin.tcData = REPLACE(REPLACE(ENTRY(2, ENTRY(1, cLin, "]"), "@"), "-0300", ""), "-0200", "").
    END.
    INPUT STREAM sDad CLOSE.

    RUN processaAppPerf (hBuffer).

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE processaAppPerf:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE iLinTot   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cProces   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cProg     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHora     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHoraI    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHoraF    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTxt      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTmp      AS CHARACTER NO-UNDO.

    DEFINE VARIABLE iHora     AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iHoraI    AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iHoraF    AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iLin      AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iLinI     AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iLinF     AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iHoraD    AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iMili     AS INTEGER   NO-UNDO.
    DEFINE VARIABLE ix        AS INTEGER   NO-UNDO.

    DEFINE BUFFER bfLin FOR ttLin.

    FIND LAST ttLin NO-LOCK NO-ERROR.
    IF  AVAILABLE ttLin THEN
        ASSIGN iLinTot = ttLin.tiLinh.

    FOR EACH ttLin EXCLUSIVE-LOCK
        BREAK BY ttLin.tcProc
              BY ttLin.tcData:
        IF  (ttLin.tiLinh MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Processando " + STRING(ttLin.tiLinh, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iLinTot, "zzz,zzz,zzz,zzz,zz9") + " linhas.").
        END.

        ASSIGN cLin    = ttLin.tcLinh
               cProces = ttLin.tcProc
               cTxt    = "".

        IF  FIRST-OF(ttLin.tcProc) THEN DO:
            FOR EACH bfLin EXCLUSIVE-LOCK
                WHERE bfLin.tcProc = ttLin.Tcproc:
                ASSIGN cLin  = bfLin.tcLinh.
                IF  NOT cLin BEGINS "["
                OR  NUM-ENTRIES(cLin, " ") < 3 THEN
                    NEXT.
                ASSIGN cHora = REPLACE(ENTRY(2, ENTRY(1, cLin, "]"), "@"), "-0300", "")
                       cHora = REPLACE(cHora, "-0200", "").
                IF  INDEX(cLin, "Server Message state = MSGSTATE_RECVFIRST") > 0
                OR  INDEX(cLin, "Server Message state = MSGSTATE_RECVLAST")  > 0
                OR  INDEX(cLin, "Server Message state = MSGSTATE_INITRQ")    > 0 THEN
                    ASSIGN cHoraI = cHora
                           iLin   = bfLin.tiLinh
                           iLinI  = iLin
                           ix     = 1.

                IF  INDEX(cLin, "(8400)") > 0
                OR  INDEX(cLin, "(8458)") > 0
                OR  INDEX(cLin, "(8401)") > 0
                OR  INDEX(cLin, "(8402)") > 0
                OR  INDEX(cLin, "(8403)") > 0 THEN
                    NEXT.

                IF  INDEX(cLin, "START.") > 0 THEN
                    ASSIGN cProg = substr(cLin, R-INDEX(cLin, ":") + 1, LENGTH(cLin)).

                ASSIGN cTmp = cLin
                       ENTRY(2, cTmp, " ") = ""
                       ENTRY(3, cTmp, " ") = ""
                       ENTRY(4, cTmp, " ") = ""
                       ENTRY(5, cTmp, " ") = "" no-error.

                ASSIGN cTxt = cTxt
                            + (IF  cTxt <> "" THEN CHR(10) ELSE "")
                            + trim(REPLACE(cTmp, "  ", " ")).
                IF  LENGTH(cTxt) > 15000 THEN DO:
                    createTTDetail (cTxt, iLinI, ix).
                    ASSIGN ix   = ix + 1
                           cTxt = "".
                END.

                IF  INDEX(cLin, "Server Message state = MSGSTATE_IDLE") > 0 THEN DO:
                    ASSIGN cHoraF = cHora
                           iLin   = bfLin.tiLinh
                           iLinF  = iLin.
                    IF  cHoraI <> ""
                    AND cHoraF <> "" THEN DO:
                        ASSIGN iHoraD = getDifTime(cHoraI, cHoraF).

                        IF  iHoraD > 0 THEN DO:
                            ASSIGN ENTRY(1, cLin, " ") = ""
                                   ENTRY(2, cLin, " ") = ""
                                   ENTRY(3, cLin, " ") = ""
                                   ENTRY(4, cLin, " ") = ""
                                   ENTRY(5, cLin, " ") = ""
                                   ENTRY(6, cLin, " ") = "" no-error.
                            IF  LENGTH(cTxt) > 0 THEN DO:
                                createTTDetail (cTxt, iLinI, ix).
                                ASSIGN ix   = ix + 1
                                       cTxt = "".
                            END.

                            RUN criaLinAppPerf (cProces, iLinI, cProg, cHoraI, cHoraF, iHoraD, "", hBuffer).
                            DELETE bfLin.

                            ASSIGN cHoraI  = ""
                                   cHoraF  = ""
                                   cProg   = ""
                                   cTxt    = "".
                        END.
                    END.
                END.
            END.
        END.
    END.
    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE criaLinAppPerf:
    DEFINE INPUT PARAMETER cProces AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER cProg   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cHoraI  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cHoraF  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iHoraD  AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER cTxt    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    IF  cTxt = ""
    OR  cTxt = ? THEN
        ASSIGN cTxt = cProg.

    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE()  = cProces.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()  = iLin.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE()  = TRIM(cProg).
    hBuffer:BUFFER-FIELD("tcHoraI"):BUFFER-VALUE() = cHoraI.
    hBuffer:BUFFER-FIELD("tcHoraF"):BUFFER-VALUE() = cHoraF.
    hBuffer:BUFFER-FIELD("tiHoraD"):BUFFER-VALUE() = iHoraD.
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()   = cTxt.
END PROCEDURE.

/* fim */
