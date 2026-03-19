/************************************************************************************************
** Procedures para Progress Memory Leak
************************************************************************************************/

PROCEDURE criaTTProgsMem:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hBuffer AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLog:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tcData", "DATE",0,"","","Data").
    ttLog:ADD-NEW-FIELD("tcHora", "CHAR",0,"X(13)","","Hora").
    ttLog:ADD-NEW-FIELD("tcTxt",  "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcLinh", "CHAR",0,"x(70)","","Conteudo").
    ttLog:ADD-NEW-FIELD("tcProc", "CHAR",0,"x(20)","","Processo").
    ttLog:ADD-NEW-FIELD("tcType", "CHAR",0,"x(15)","","","Tipo!Objeto").
    ttLog:ADD-NEW-FIELD("tcHand", "CHAR",0,"x(06)","","Handle").
    ttLog:ADD-NEW-FIELD("tcCate", "CHAR",0,"x(15)","","Categoria").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("bytcData", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("bytcData", "tcData").
    ttLog:ADD-INDEX-FIELD("bytcData", "tcHora").

    ttLog:ADD-NEW-INDEX("byhandle", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("byhandle", "tcHand").

    ttLog:ADD-NEW-INDEX("bysession", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("bysession", "tcProc").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hBuffer = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logProgsMem:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cChave    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBrowse   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBuffer   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hTTLog    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE lOrdem    AS LOGICAL   NO-UNDO INITIAL TRUE.

    DEFINE FRAME f-log
        dDatIni    AT ROW 02.5 COL 3
        dDatFim    SPACE(2)
        cHorIni
        cHorFim    SPACE(2)
        cbFilter
        cFilter    VIEW-AS FILL-IN SIZE 47 BY 1 NO-LABELS
        btFilter   btClear
        cDados     NO-LABELS AT ROW 19.5 COL 3
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTProgsMem (OUTPUT hTTLog, OUTPUT hBuffer).

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
           VISIBLE          = YES
           SENSITIVE        = NO
           SEPARATORS       = TRUE
           COLUMN-RESIZABLE = TRUE.

    /* adiciona as colunas do browse */
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcData")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHora")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcProc")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcType")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHand")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcCate")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcLinh")).

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER   NO-UNDO.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_MemoryLeak.log".
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

        DEFINE BUFFER bfDet FOR ttDetail.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_MemoryLeak_tmp.log".
        OUTPUT TO VALUE(cArqPrint).
        PUT UNFORMATTED
            hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()
            SKIP.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  MOUSE-SELECT-CLICK OF hBrowse DO:
        IF  hBuffer:AVAILABLE
        AND hBrowse:CURRENT-COLUMN <> ? THEN
            APPLY "recall" TO FRAME f-log.
    END.

    ON  RECALL OF FRAME f-log DO:
        DEFINE VARIABLE cQuery AS CHARACTER NO-UNDO.

        ASSIGN cQuery = "FOR EACH ttLog "
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
        IF  hBuffer:AVAILABLE THEN
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE().
        ELSE
            ASSIGN cDados:SCREEN-VALUE IN FRAME f-log = "".
    END.

    ON  CHOOSE OF btClear DO:
        ASSIGN cFilter:SCREEN-VALUE = ""
               cChave = "".
        APPLY "CHOOSE" TO btFilter.
    END.

    ON  CHOOSE OF btFilter DO:
        ASSIGN cbFilter
               cFilter
               dDatIni
               dDatFim
               cHorIni
               cHorFim.

        ASSIGN cChave = "".
        IF  dDatIni <> 01/01/1800
        OR  dDatFim <> 12/31/9999 THEN
            ASSIGN cChave = (IF cChave <> "" THEN " and " ELSE " Where ")
                          + "     ttLog.tcData >= " + string(dDatIni,"99/99/9999")
                          + " and ttLog.tcData <= " + string(dDatFim,"99/99/9999").

        IF  cHorIni <> "000000"
        OR  cHorFim <> "999999" THEN
            ASSIGN cChave = (IF cChave <> "" THEN " and " ELSE " Where ")
                          + "     ttLog.tcHora >= '" + string(cHorIni,"99:99:99") + ",000'"
                          + " and ttLog.tcHora <= '" + string(cHorFim,"99:99:99") + ",999'".

        CASE cbFilter:
            WHEN "Processo" THEN ASSIGN cChave = (IF cChave <> "" THEN " and " ELSE " Where ") + " ttLog.tcProc begins '" + cFilter + "'".
            WHEN "Conteudo" THEN ASSIGN cChave = (IF cChave <> "" THEN " and " ELSE " Where ") + " ttLog.tcLinh matches '*" + cFilter + "*'".
        END CASE.

        APPLY "recall" TO FRAME f-log.
    END.

    ASSIGN cDados:READ-ONLY = TRUE
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse.

    ASSIGN cbFilter:list-items = "Processo,Conteudo".

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaProgsMem (pDir, pArq, hBuffer).

    APPLY "CHOOSE" TO btFilter.

    SESSION:SET-WAIT-STATE("").

     IF  NOT hBuffer:AVAILABLE THEN DO:
        MESSAGE "Aparentemente nao consegui detectar nenhuma tag para detectar objetos perdidos na memoria." SKIP
                "Favor verificar se a configuracao do log esta incluida as tags 'DynObjects.DB,DynObjects.XML,DynObjects.Other,DynObjects.CLASS,DynObjects.UI' no LogEntryTypes."
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
        DELETE OBJECT hQuery NO-ERROR.
        DELETE OBJECT hTTLog NO-ERROR.
        DELETE OBJECT hBrowse NO-ERROR.
        DELETE OBJECT hBuffer NO-ERROR.
    END.
END PROCEDURE.

PROCEDURE importaProgsMem:
    DEFINE INPUT PARAMETER cDir    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cArq    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cArq2     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iLinOrg   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iFileLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iProcLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE hBuf2     AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.

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

        IF  TRIM(cLin) = ""
        OR  LENGTH(cLin) < 50 THEN
            NEXT.

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.

        IF  INDEX(cLin, "DYNOBJECTS") = 0 THEN
            NEXT.

        IF  NOT (INDEX(cLin, "Created") > 0
        OR  INDEX(cLin, "Deleted") > 0) THEN
            NEXT.

        DO WHILE INDEX(cLin, "  ") > 0:
            ASSIGN cLin = REPLACE(cLin, "  ", " ").
        END.

        RUN criaLinProgsMem(cLin, hBuffer).
    END.
    INPUT STREAM sDad CLOSE.

    /* cria a query */
    CREATE QUERY hQuery.
    hQuery:SET-BUFFERS(hBuffer).
    CREATE BUFFER hBuf2 FOR TABLE hBuffer.
    hQuery:QUERY-PREPARE("for each ttLog "
                        + "where ttLog.tcCate begins 'Created' "
                        + "BY ttLog.tcHand BY ttLog.tcData").
    hQuery:QUERY-OPEN().
    hQuery:GET-FIRST().
    DO  WHILE NOT hQuery:QUERY-OFF-END:
        /* filtra o que ficou na memoria */
        hBuf2:FIND-FIRST("WHERE ttLog.tcCate begins 'Deleted' "
                        + "AND ttLog.tcHand = '" + hBuffer:BUFFER-FIELD("tcHand"):BUFFER-VALUE() + "' "
                        + "AND ttLog.tcData >= " + string(hBuffer:BUFFER-FIELD("tcData"):BUFFER-VALUE(), "99/99/9999") + " "
                        + "AND recid(ttLog) <> " + string(hBuffer:ROWID), SHARE-LOCK) NO-ERROR.
        IF  hBuf2:AVAILABLE THEN DO:
            hBuf2:BUFFER-DELETE().
            hBuffer:BUFFER-DELETE().
        END.
        hQuery:GET-NEXT().
    END.
    DELETE OBJECT hQuery.
    DELETE OBJECT hBuf2.

    HIDE MESSAGE NO-PAUSE.

    PUBLISH "showMessage" FROM THIS-PROCEDURE ("Esses objetos no browse foram criados e nao foram eliminados, sao objetos perdidos que causam o memory-leak.").
END PROCEDURE.

PROCEDURE criaLinProgsMem:
    DEFINE INPUT PARAMETER cLin    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cProces AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cData   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHora   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cCateg  AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cType   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHandle AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cTxt    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE dData   AS DATE      NO-UNDO.

    ASSIGN cTxt    = cLin
           cProces = ENTRY(2, cLin, " ") + " " + entry(3, cLin, " ")
           cData   = ENTRY(2, ENTRY(1, cLin, "@"), "[")
           cHora   = REPLACE(ENTRY(2, ENTRY(1, cLin, "]"), "@"), "-0300", "")
           cHora   = REPLACE(cHora, "-0200", "")
           cCateg  = ENTRY(7, cLin, " ")
           cType   = ENTRY(8, cLin, " ")
           cHandle = ENTRY(2, ENTRY(9, cLin, " "), ":") NO-ERROR.
           cLin    = ENTRY(2, clin, "(").

    IF  NUM-ENTRIES(cData, "/") > 1 THEN
        ASSIGN dData = DATE(ENTRY(3, cData, "/") + "/" + entry(2, cData, "/") + "/" + entry(1, cData, "/")) no-error.

    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE() = cProces.
    hBuffer:BUFFER-FIELD("tcData"):BUFFER-VALUE() = dData.
    hBuffer:BUFFER-FIELD("tcHora"):BUFFER-VALUE() = cHora.
    hBuffer:BUFFER-FIELD("tcType"):BUFFER-VALUE() = cType.
    hBuffer:BUFFER-FIELD("tcHand"):BUFFER-VALUE() = cHandle.
    hBuffer:BUFFER-FIELD("tcCate"):BUFFER-VALUE() = cCateg.
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()  = cTxt.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE() = cLin.
END PROCEDURE.

/* fim */
