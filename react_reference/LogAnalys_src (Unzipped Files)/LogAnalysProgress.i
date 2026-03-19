/************************************************************************************************
** Procedures para Progress
************************************************************************************************/

PROCEDURE criaTTProgs:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hLogBuf AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLog:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh", "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcData", "DATE",0,"","","Data").
    ttLog:ADD-NEW-FIELD("tcHora", "CHAR",0,"X(13)","","Hora").
    ttLog:ADD-NEW-FIELD("tcTxt",  "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcLinh", "CHAR",0,"x(90)","","Conteudo").
    ttLog:ADD-NEW-FIELD("tcCate", "CHAR",0,"x(20)","","Categoria").
    ttLog:ADD-NEW-FIELD("tcProc", "CHAR",0,"x(10)","","Processo").
    ttLog:ADD-NEW-FIELD("tcProg", "CHAR",0,"x(15)","","Programa").
    ttLog:ADD-NEW-FIELD("tiProg", "CHAR",0,"","","Linha Prog").
    ttLog:ADD-NEW-FIELD("tcPI",   "CHAR",0,"x(15)","","Procedure").
 
    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcProc").
    ttLog:ADD-INDEX-FIELD("codigo", "tcCate").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    ttLog:ADD-NEW-INDEX("dataProc", NO /* unique*/, NO /* primario */).
    ttLog:ADD-INDEX-FIELD("dataProc", "tcProc").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcCate").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcData").
    ttLog:ADD-INDEX-FIELD("dataProc", "tcHora").
    ttLog:ADD-INDEX-FIELD("dataProc", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hLogBuf = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logProgs:
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
        cbTypeLst  LABEL "Processo" AT ROW 01.5 COL 3
        cbCatLst
        btCorrigir AT ROW 01.5 COL 152
        dDatIni    AT ROW 02.5 COL 3
        dDatFim    SPACE(2)
        cHorIni
        cHorFim    SPACE(2)
        cbFilter
        cFilter    VIEW-AS FILL-IN SIZE 47 BY 1 NO-LABELS
        btFilter   btClear
        bDetail    AT ROW 19.5 COL 3
        cDados     NO-LABELS AT ROW 19.5 COL 18
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTProgs (OUTPUT hTTLog, OUTPUT hBuffer).

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
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiLinh")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcData")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcHora")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcProg")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiProg")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcPI")).
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

        ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcProc = '" + cbTypeLst + "'"
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
        ASSIGN cbFilter
               cFilter
               dDatIni
               dDatFim
               cHorIni
               cHorFim.

        ASSIGN cChave = "".
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

        CASE cbFilter:
            WHEN "Programa" THEN ASSIGN cChave = cChave + " and ttLog.tcProg begins '" + cFilter + "'".
            WHEN "PI"       THEN ASSIGN cChave = cChave + " and ttLog.tcPI begins '" + cFilter + "'".
            WHEN "Conteudo" THEN ASSIGN cChave = cChave + " and ttLog.tcLinh matches '*" + cFilter + "*'".
        END CASE.

        APPLY "value-changed" TO cbCatLst.
    END.

    ON  CHOOSE OF btCorrigir DO:
        RUN showFix (cDir, cArq).
    END.

    ASSIGN cDados:READ-ONLY = TRUE
           hFrame           = FRAME f-log:Handle
           hDados           = cDados:handle
           hBrw             = hBrowse
           hDet             = BROWSE bDetail:handle.

    ASSIGN cbFilter:list-items = "Programa,PI,Conteudo".

    DISPLAY dDatIni dDatFim cHorIni cHorFim WITH FRAME f-log.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaProgs (pDir, pArq, hBuffer).

    ASSIGN cbTypeLst:LIST-ITEMS = getListType().
    IF  CAN-DO(cbTypeLst:LIST-ITEMS, "ERROR") THEN
        ASSIGN cbTypeLst:SCREEN-VALUE = "ERROR".
    ELSE
        ASSIGN cbTypeLst:SCREEN-VALUE = ENTRY(1,cbTypeLst:LIST-ITEMS).

    APPLY "value-changed" TO cbTypeLst.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.

    FIND FIRST ttFix NO-LOCK NO-ERROR.
    IF  AVAILABLE ttFix THEN
        PUBLISH "showMessage" FROM THIS-PROCEDURE ("Dica: Consegui identificar alguns problemas, clique no botao 'Identifcar Problemas' para analisa-los.").
    ASSIGN btCorrigir:visible = (AVAILABLE ttFix).

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

PROCEDURE importaProgs:
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

        IF  TRIM(cLin) = ""
        OR  LENGTH(cLin) < 50 THEN
            NEXT.

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.

        CREATE ttLin.
        ASSIGN ttLin.tcLinh = cLin
               ttLin.tiLinh = iLinOrg.
    END.
    INPUT STREAM sDad CLOSE.

    RUN processaProgs (hBuffer).

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE processaProgs:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE iLinTot   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cProces   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cProg     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cPI       AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cNLin     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cCateg    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cData     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cHora     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cErro     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iErro     AS INTEGER   NO-UNDO.
    DEFINE VARIABLE ix        AS INTEGER   NO-UNDO.

    DEFINE BUFFER bfLin FOR ttLin.

    FIND LAST ttLin NO-LOCK NO-ERROR.
    IF  AVAILABLE ttLin THEN
        ASSIGN iLinTot = ttLin.tiLinh.

    FOR EACH ttLin EXCLUSIVE-LOCK:
        IF  (ttLin.tiLinh MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Processando " + STRING(ttLin.tiLinh, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iLinTot, "zzz,zzz,zzz,zzz,zz9") + " linhas.").
        END.

        ASSIGN cLin = ttLin.tcLinh.

        IF  TRIM(cLin) BEGINS "["
        AND NUM-ENTRIES(cLin, "/") > 2
        AND NUM-ENTRIES(cLin, " ") > 4 THEN DO:
            /* zera as variaveis utilizadas */
            ASSIGN cProces = ""
                   cProg   = ""
                   cNLin   = ""
                   cPI     = ""
                   cCateg  = ""
                   cData   = ""
                   cHora   = ""
                   cLin2   = cLin.

            /* Processo, data, hora e categoria */
            ASSIGN cProces = ENTRY(2, cLin, " ")
                   cData   = ENTRY(2, ENTRY(1, cLin, "@"), "[")
                   cHora   = REPLACE(ENTRY(2, ENTRY(1, cLin, "]"), "@"), "-0300", "")
                   cHora   = REPLACE(cHora, "-0200", "")
                   cCateg  = ENTRY(6, cLin, " ").

            /* se a categoria for '--' e Roles:, ignora a linha */
            IF  (cCateg BEGINS "--"
            OR   cCateg = "CONN")
            AND INDEX(ttLin.tcLinh, " Roles: ") > 0 THEN DO:
                DELETE ttLin.
                NEXT.
            END.

            /* se a categoria for '--' assume como mensagem */
            IF  cCateg BEGINS "--" THEN
                ASSIGN cCateg = "MESSAGE".

            /* retira a parte inicial da linha pois ja esta categorizado e temos a data, hora e processo */
            ASSIGN ENTRY(1, cLin, " ") = ""
                   ENTRY(2, cLin, " ") = ""
                   ENTRY(3, cLin, " ") = ""
                   ENTRY(4, cLin, " ") = ""
                   ENTRY(5, cLin, " ") = ""
                   ENTRY(6, cLin, " ") = ""
                   cLin                = TRIM(cLin).

            IF  cLin BEGINS "requestID="
            OR  INDEX(cLin, "dlc1") > 0
            OR  INDEX(cLin, "(12699)") > 0 THEN
                NEXT.

            /* ignora arquivos de trabalho lbi, str e rcd */
            IF  cCateg BEGINS "FILEID" THEN DO:
                ASSIGN cLin3 = REPLACE(cLin, "~\", "/").
                IF  (INDEX(cLin3, "/srt") > 0
                OR   INDEX(cLin3, "/lbi") > 0
                OR   INDEX(cLin3, "/rcd") > 0) THEN
                     NEXT.
            END.

            /* para WebSpeed */
            IF  cCateg = "QRYINFO" THEN DO:
                ASSIGN ix = 1.
                FOR EACH bfLin EXCLUSIVE-LOCK
                    WHERE bfLin.tiLinh > ttLin.tiLinh:
                    ASSIGN cLin3 = TRIM(bfLin.tcLinh).
                    IF  INDEX(cLin3, " QRYINFO ") = 0 
                    OR  (INDEX(cLin2, " Query Plan:") > 0 
                    AND  INDEX(cLin3, " Query Plan:") > 0) THEN
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
                IF  LENGTH(cLin2) > 0 THEN DO:
                    createTTDetail (cLin2, ttLin.tiLinh, ix).
                    ASSIGN ix    = ix + 1
                           cLin2 = "".
                END.
                RUN criaLinProgs (cProces, cData, cHora, cProg, cNLin, cPI, cCateg, cLin, "", ttLin.tiLinh, hBuffer).
                DELETE ttLin.
                NEXT.
            END.

            IF  (cCateg = "MESSAGE"
            AND INDEX(cLin2, " -- ") > 0
            AND INDEX(cLin2, "(")    > 0
            AND INDEX(cLin2, ")")    > 0) 
            OR  INDEX(cLin2, "SYSTEM ERROR: ") > 0 THEN DO:
                IF  INDEX(cLin2, "(293)")   > 0
                OR  INDEX(cLin2, "(1006)")  > 0
                OR  INDEX(cLin2, "(1005)")  > 0
                OR  INDEX(cLin2, "(1004)")  > 0
                OR  INDEX(cLin2, "(12272)") > 0
                OR  INDEX(cLin2, "(2888)")  > 0
                OR  INDEX(cLin2, "(14631)")  > 0
                OR  (INDEX(cLin2, "exclusiva") > 0 AND index(cLin2, "violada") > 0)
                OR  index(cLin2, "Schema holder does not match database schema") > 0
                OR  INDEX(cLin2, "SYSTEM ERROR: ") > 0 THEN
                    ASSIGN cCateg = "ERROR".
                
                IF  (INDEX(cLin2, "exclusiva") > 0 
                AND index(cLin2, "violada") > 0)
                OR  index(cLin2, "Schema holder does not match database schema") > 0
                THEN DO:
                    ASSIGN cCateg = "ERROR"
                           ix     = 1.
                    FOR EACH bfLin EXCLUSIVE-LOCK
                        WHERE bfLin.tiLinh > ttLin.tiLinh:
                        ASSIGN cLin3 = TRIM(bfLin.tcLinh).
                        IF  INDEX(cLin3, " -- ") = 0 THEN
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
                    IF  LENGTH(cLin2) > 0 THEN DO:
                        createTTDetail (cLin2, ttLin.tiLinh, ix).
                        ASSIGN ix    = ix + 1
                               cLin2 = "".
                    END.
                    RUN criaLinProgs (cProces, cData, cHora, cProg, cNLin, cPI, cCateg, cLin, "", ttLin.tiLinh, hBuffer).
                    DELETE ttLin.
                    NEXT.
                END.
                ELSE DO:
                    ASSIGN cErro = REPLACE(substr(cLin2, R-INDEX(cLin2, "(") + 1, LENGTH(cLin2)), ")", "").
                    IF  INDEX(cErro, "Line:") > 0 THEN DO: 
                        ASSIGN iErro = INTEGER(cErro) no-error.
                        IF  iErro > 0 THEN DO:
                            ASSIGN cCateg = "ERROR"
                                   ix     = 1.
                            FOR EACH bfLin EXCLUSIVE-LOCK
                                WHERE bfLin.tiLinh > ttLin.tiLinh:
                                ASSIGN cLin3 = TRIM(bfLin.tcLinh).
                                IF  INDEX(cLin3, " -- ") = 0 THEN
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
                            IF  LENGTH(cLin2) > 0 THEN DO:
                                createTTDetail (cLin2, ttLin.tiLinh, ix).
                                ASSIGN ix    = ix + 1
                                       cLin2 = "".
                            END.
                            RUN criaLinProgs (cProces, cData, cHora, cProg, cNLin, cPI, cCateg, cLin, "", ttLin.tiLinh, hBuffer).
                            DELETE ttLin.
                            NEXT.
                        END.
                    END.
                END.
            END.

            /* se tiver .eai. assume a categoria como eai */
            IF  INDEX(cLin, ".eai.") > 0 
            AND INDEX(cLin2, "(")    = 0
            AND INDEX(cLin2, ")")    = 0 THEN 
                ASSIGN cCateg = "EAI2".

            /* pega o nome do programa, procedure e linha */
            IF  R-INDEX(cLin, "[") > 0 THEN DO:
                ASSIGN cLin3 = substr(cLin, R-INDEX(cLin, "["), LENGTH(cLin))
                       cLin  = REPLACE(cLin, cLin3, "")
                       cLin3 = REPLACE(cLin3, "Main Block", "MainBlock")
                       cLin3 = REPLACE(cLin3, "[", "")
                       cLin3 = REPLACE(cLin3, "~\", "/")
                       cPI   = ENTRY(1, cLin3, " ")
                       cPI   = REPLACE(ENTRY(NUM-ENTRIES(cPI,"/"), cPI, "/"),"]","")
                       cProg = ENTRY(3, cLin3, " ")
                       cProg = ENTRY(NUM-ENTRIES(cProg,"/"), cProg, "/")
                       cNLin = REPLACE(ENTRY(5, cLin3, " "),"]","") no-error.
                IF  cProg =  ""
                AND cPI   <> "" THEN
                    ASSIGN cProg = cPI
                           cPI   = "".

                /* agrupa de acordo com a necessidade */
                IF  INDEX(cLin3, "btb908z") > 0 THEN
                    ASSIGN cCateg = "RPW".
                IF  INDEX(cLin3, "btb962") > 0 THEN
                    ASSIGN cCateg = "EMPRESA".
                IF  INDEX(cLin3, "men906") > 0 THEN
                    ASSIGN cCateg = "DI".
                IF  INDEX(cLin3, "aup/") > 0 THEN
                    ASSIGN cCateg = "AUDITTRAIL".
                IF  INDEX(cLin3, "utapi033") > 0
                OR  INDEX(cLin3, ".iface.")  > 0
                OR  INDEX(cLin3, ".ms.")     > 0
                OR  INDEX(cLin3, ".libre.")  > 0
                OR  INDEX(cLin3, "btb944za") > 0
                OR  INDEX(cLin3, "utapi013") > 0 THEN
                    ASSIGN cCateg = "OFFICE".
            END.

            RUN criaLinProgs (cProces, cData, cHora, cProg, cNLin, cPI, cCateg, cLin, "", ttLin.tiLinh, hBuffer).
            createTTDetail (ttLin.tcLinh, ttLin.tiLinh, 1).
            DELETE ttLin.
        END.
    END.

    RUN atualizaFix.

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE criaLinProgs:
    DEFINE INPUT PARAMETER cProces AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cData   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cHora   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cProg   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cNLin   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cPI     AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cCateg  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cLin    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cTxt    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE dData    AS DATE      NO-UNDO.

    IF  NUM-ENTRIES(cData, "/") > 1 THEN
        ASSIGN dData = DATE(ENTRY(3, cData, "/") + "/" + entry(2, cData, "/") + "/" + entry(1, cData, "/")) no-error.

    /* cria a linha com a informacao */
    IF  cTxt = ""
    OR  cTxt = ? THEN
        ASSIGN cTxt = cLin.

    /* verifica se existe fix para o problema */
    RUN verifyFixProgs (cTxt, iLin).

    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tcProc"):BUFFER-VALUE() = cProces.
    hBuffer:BUFFER-FIELD("tcData"):BUFFER-VALUE() = dData.
    hBuffer:BUFFER-FIELD("tcHora"):BUFFER-VALUE() = cHora.
    hBuffer:BUFFER-FIELD("tcProg"):BUFFER-VALUE() = cProg.
    hBuffer:BUFFER-FIELD("tiProg"):BUFFER-VALUE() = cNLin.
    hBuffer:BUFFER-FIELD("tcPI"):BUFFER-VALUE()   = cPI.
    hBuffer:BUFFER-FIELD("tcCate"):BUFFER-VALUE() = cCateg.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE() = cLin.
    hBuffer:BUFFER-FIELD("tcTxt"):BUFFER-VALUE()  = cTxt.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() = iLin.

    RUN criaCateg (cProces, cCateg).
END PROCEDURE.

PROCEDURE verifyFixProgs:
    DEFINE INPUT PARAMETER cLin   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin   AS INTEGER   NO-UNDO.

    DEFINE VARIABLE cTmp          AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cErro         AS CHARACTER NO-UNDO.

    /* Fix 1 - programa nao encontrado */
    IF  INDEX(cLin, "(293)") > 0 THEN DO:
        ASSIGN cTmp = cLin.
        IF  NUM-ENTRIES(cTmp, "~"") > 1 THEN
            ASSIGN cTmp = ENTRY(2, cTmp, "~"").
        RUN criaFix("Nao foi possivel localizar o programa ~"" + cTmp + "~"",
                    "Verifique se o programa realmente existe ou se esta no PROPATH.",
                    iLin).
    END.

    /* Fix 2 - banco de dados nao conectado */
    IF  INDEX(cLin, "(1006)") > 0 THEN DO:
        ASSIGN cTmp = cLin.
        IF  NUM-ENTRIES(cTmp, "~"") > 1 THEN
            ASSIGN cTmp = ENTRY(2, cTmp, "~"").
        RUN criaFix("Um banco de dados nao foi conectado durante a execucao.",
                    "Verifique o cadastro de banco de dados da empresa ou o '.pf' se este banco esta correto.",
                    iLin).
    END.

    /* Fix 3 - problemas de passagem de parametros */
    IF  INDEX(cLin, "(1005)") > 0
    OR  INDEX(cLin, "(1004)") > 0 THEN DO:
        RUN criaFix("Tem um programa que esta recebendo parametros mas nao esta esperando nenhum.",
                    "Verifique o programa chamado ou o programa chamador pois ele pode estar desatualizado ou recebendo parametros que nao sao necessarios.",
                    iLin).
    END.

    /* Fix 4 - versao invalida de progress */
    IF  INDEX(cLin, "(2888)") > 0 THEN DO:
        RUN criaFix("Programa compilado contra a versao errada do progress.",
                    "Verifique o programa chamado ou o programa chamador pois ele foi compilado contra a versao errada do progress e devera ser recompilado com o progress atual.",
                    iLin).
    END.

    /* Fix 5 - problemas na passagem de parametros */
    IF  INDEX(cLin, "(12272)") > 0 THEN DO:
        RUN criaFix("Ocorreu problemas na passagem de parametros.",
                    "Verifique o programa chamado ou o programa chamador pois ele esta passando errada os parametros para o programa filho.",
                    iLin).
    END.

    /* Fix 6 - base do EAI desconectada ou problema em propath com o EAI */
    IF  INDEX(cLin, "(14631)") > 0 
    AND INDEX(cLin, ".eai.") > 0 THEN DO:
        RUN criaFix("Ocorreu problemas com o EAI.",
                    "Verifique se o banco do EAI esta conectado e se os programas do EAI estao no PROPATH.",
                    iLin).
    END.

    /* Fix 7 - system error */
    IF  INDEX(cLin, "SYSTEM ERROR:") > 0 THEN DO:
        RUN criaFix("Ocorreu um SYSTEM ERROR durante a execucao do programa.",
                    "Verifique o arquivo protrace.99999 (onde 99999 sera numero da conexao com banco de dados) para identificar o causador desse System Error.",
                    iLin).
    END.
    
    /* Fix 8 - Constraint violada */
    IF  INDEX(cLin, "exclusiva") > 0 
    AND index(cLin, "violada") > 0 THEN DO:
        ASSIGN cErro = ENTRY(1, substr(cLin, R-INDEX(cLin, "(") + 1, LENGTH(cLin)), ")") no-error.
        IF  cErro = ? THEN 
            ASSIGN cErro = "Nao foi possivel pegar o nome, verifique nas linhas originais do log".
        RUN criaFix("Ocorreu um problema de violacao de constraint ORACLE/MSS durante a execucao do programa.",
                    "Verifique o indice '" + cErro + "' pois ‚ um indice unico e mesmo esta com dados duplicados ou os seus campos onde nao foram totalmente preenchidos.",
                    iLin).
    END.

    /* Fix 9 - erro de schema holder */
    IF  INDEX(cLin, "Schema holder does not match database schema") > 0 THEN DO:
        RUN criaFix("Ocorreu um problema no Schema Holder onde um ou mais campos nao estao batendo com o cadastrado no banco de dados.",
                    "Faca uma comparacao entre o seu Schema Holder e o banco de dados que esta ocorrendo o erro.",
                    iLin).
    END.
END PROCEDURE.

/* fim */
