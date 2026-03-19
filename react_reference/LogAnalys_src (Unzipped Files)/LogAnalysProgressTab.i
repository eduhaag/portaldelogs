/************************************************************************************************
** Procedures para Progress Tabanalys
************************************************************************************************/

PROCEDURE criaTTProgsTab:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hLogBuf AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLogTab:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh",  "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcCate",  "CHAR",0,"","","Categoria").
    ttLog:ADD-NEW-FIELD("tcTab",   "CHAR",0,"x(40)","","Tabela").
    ttLog:ADD-NEW-FIELD("tcInd",   "CHAR",0,"x(40)","","Indice").
    ttLog:ADD-NEW-FIELD("tiReg",   "INT64",0,"","","Registros").
    ttLog:ADD-NEW-FIELD("tiField", "INTE",0,">>>9","","Campos").
    ttLog:ADD-NEW-FIELD("tiFact",  "DECIMAL",0,">>9.9","","Factor").
    ttLog:ADD-NEW-FIELD("tcLinh",  "CHAR",0,"","","Detalhes").
    ttLog:ADD-NEW-FIELD("tcObs",   "CHAR",0,"x(60)","","Observacao").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcCate").
    ttLog:ADD-INDEX-FIELD("codigo", "tcTab").
    ttLog:ADD-INDEX-FIELD("codigo", "tcInd").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hLogBuf = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logProgsTab:
    DEFINE INPUT PARAMETER pDir AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER pArq AS CHARACTER NO-UNDO.

    DEFINE VARIABLE cChave    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE hQuery    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBrowse   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hBuffer   AS HANDLE    NO-UNDO.
    DEFINE VARIABLE hTTLog    AS HANDLE    NO-UNDO.
    DEFINE VARIABLE lOrdem    AS LOGICAL   NO-UNDO INITIAL TRUE.
    DEFINE VARIABLE cCab      AS CHARACTER NO-UNDO.
    
    DEFINE VARIABLE rsCatLst  AS CHARACTER NO-UNDO
                                VIEW-AS RADIO-SET HORIZONTAL RADIO-BUTTONS "Tabela","tab","Indices","ind".

    DEFINE FRAME f-log
        rsCatLst   LABEL "Tipo" AT ROW 01.5 COL 3
        cFilter    VIEW-AS FILL-IN SIZE 47 BY 1 NO-LABELS AT ROW 02.5 COL 3
        btFilter   btClear
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTProgsTab (OUTPUT hTTLog, OUTPUT hBuffer).

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
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcTab")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcInd")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiReg")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiField")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiFact")).
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcObs")).

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        ASSIGN rsCatLst.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + rsCatLst + ".log".
        OUTPUT TO VALUE(cArqPrint).
        /* cabecalho */
        PUT UNFORMATTED "Lin;Tabela;".
        IF  rsCatLst = "ind" THEN 
            PUT UNFORMATTED "Indice;Campos;".
        ELSE
            PUT UNFORMATTED "Registros;".
        PUT UNFORMATTED "Factor;Observacao" SKIP.
        
        hQuery:GET-FIRST().
        DO  WHILE NOT hQuery:QUERY-OFF-END:
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcTab"):BUFFER-VALUE()  ";".
            IF  rsCatLst = "ind" THEN 
                PUT UNFORMATTED
                    hBuffer:BUFFER-FIELD("tcInd"):BUFFER-VALUE() ";"
                    hBuffer:BUFFER-FIELD("tiField"):BUFFER-VALUE() ";".
            ELSE
                PUT UNFORMATTED
                    hBuffer:BUFFER-FIELD("tiReg"):BUFFER-VALUE() ";".
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tiFact"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcObs"):BUFFER-VALUE() SKIP.
            hQuery:GET-NEXT().
        END.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.

    ON  CHOOSE OF btClip IN FRAME f-log DO:
        DEFINE VARIABLE cCab AS CHARACTER NO-UNDO.
        
        ASSIGN rsCatLst.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.
        
        ASSIGN cCab = "Lin;Tabela;".
        
        ASSIGN cLin = STRING(hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()) + ";"
                    + hBuffer:BUFFER-FIELD("tcTab"):BUFFER-VALUE() + ";".
        IF  rsCatLst = "ind" THEN 
            ASSIGN cLin = cLin 
                        + hBuffer:BUFFER-FIELD("tcInd"):BUFFER-VALUE() + ";"
                        + string(hBuffer:BUFFER-FIELD("tiField"):BUFFER-VALUE()) + ";"
                   cCab = cCab + "Indice;Campos;".
        ELSE
            ASSIGN cLin = cLin 
                        + string(hBuffer:BUFFER-FIELD("tiReg"):BUFFER-VALUE()) + ";"
                   cCab = cCab + "Registros;".
        ASSIGN cLin = cLin 
                    + string(hBuffer:BUFFER-FIELD("tiFact"):BUFFER-VALUE()) + ";" 
                    + hBuffer:BUFFER-FIELD("tcObs"):BUFFER-VALUE() + chr(10).
               cCab = cCab + "Factor;Observacao".
        
        ASSIGN CLIPBOARD:VALUE = cCab + chr(10) + cLin.
    END.

    ON  CHOOSE OF btNotepad IN FRAME f-log DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        IF  NOT hBuffer:AVAILABLE THEN
            RETURN.

        ASSIGN rsCatLst.

        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + rsCatLst + "_tmp.log".
        OUTPUT TO VALUE(cArqPrint).
        /* cabecalho */
        PUT UNFORMATTED "Lin;Tabela;".
        IF  rsCatLst = "ind" THEN 
            PUT UNFORMATTED "Indice;Campos;".
        ELSE
            PUT UNFORMATTED "Registros;".
        PUT UNFORMATTED "Factor;Observacao" SKIP.

        PUT UNFORMATTED
            hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() ";"
            hBuffer:BUFFER-FIELD("tcTab"):BUFFER-VALUE()  ";".
        IF  rsCatLst = "ind" THEN 
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tcInd"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tiField"):BUFFER-VALUE() ";".
        ELSE
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tiReg"):BUFFER-VALUE() ";".
        PUT UNFORMATTED
            hBuffer:BUFFER-FIELD("tiFact"):BUFFER-VALUE() ";"
            hBuffer:BUFFER-FIELD("tcObs"):BUFFER-VALUE() SKIP.
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.
    
    ON  VALUE-CHANGED OF rsCatLst DO:
        ASSIGN rsCatLst. 
        ASSIGN lOrdem = TRUE.

        hBrowse:get-browse-column(3):visible = (rsCatLst = "ind"). /* tcInd */
        hBrowse:get-browse-column(4):visible = (rsCatLst = "tab"). /* tiReg */
        hBrowse:get-browse-column(5):visible = (rsCatLst = "ind"). /* tiField */

        APPLY "recall" TO FRAME f-log.
    END.
        
    ON  MOUSE-SELECT-CLICK OF hBrowse DO:
        IF  hBuffer:AVAILABLE
        AND hBrowse:CURRENT-COLUMN <> ? THEN
            APPLY "recall" TO FRAME f-log.
    END.
    
    ON  RECALL OF FRAME f-log DO:
        DEFINE VARIABLE cQuery AS CHARACTER NO-UNDO.

        ASSIGN rsCatLst.

        ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcCate = '" + rsCatLst + "'"
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

    ON  CHOOSE OF btClear DO:
        ASSIGN cFilter:SCREEN-VALUE = ""
               cChave = "".
        APPLY "value-changed" TO rsCatLst.
    END.
    
    ON  CHOOSE OF btFilter
    OR  RETURN OF cFilter DO:
        ASSIGN cFilter.

        ASSIGN cChave = " and ttLog.tcLinh matches '*" + cFilter + "*'".

        APPLY "value-changed" TO rsCatLst.
    END.
        
    ASSIGN hFrame           = FRAME f-log:Handle
           hBrw             = hBrowse.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaProgsTab (pDir, pArq, hBuffer).

    APPLY "value-changed" TO rsCatLst.

    SESSION:SET-WAIT-STATE("").
    HIDE MESSAGE NO-PAUSE.
    
    APPLY "WINDOW-RESIZED" TO CURRENT-WINDOW.
        
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

PROCEDURE importaProgsTab:
    DEFINE INPUT PARAMETER cDir    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cArq    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cArq2     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iLinOrg   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iFileLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iProcLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE lRecord   AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE lIndex    AS LOGICAL   NO-UNDO.

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
        OR  LEFT-TRIM(cLin) BEGINS fill("-", 15) 
        OR  cLin BEGINS "Table" 
        OR  LEFT-TRIM(cLIn) BEGINS "-Record Size"
        OR  cLin BEGINS "Subtotals:" 
        OR  INDEX(cLin, "RM block") > 0 
        OR  INDEX(cLin, "free block") > 0 
        OR  INDEX(cLin, "index table block") > 0 
        OR  INDEX(cLin, "sequence block") > 0 
        OR  INDEX(cLin, "empty block") > 0 
        OR  INDEX(cLin, "total block") > 0 
        OR  (INDEX(cLin, "index block") > 0 AND INDEX(cLin, "SUMMARY") = 0)
        OR  cLin BEGINS "Size key:"
        OR  INDEX(cLin,"bytes") > 0
        OR  INDEX(cLin, "RESUMO DO BLOCO DE") > 0 THEN
            NEXT.

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.

        IF  LEFT-TRIM(cLin) BEGINS "RECORD BLOCK SUMMARY" THEN DO:
            ASSIGN lRecord = TRUE.
            NEXT.
        END.

        IF  LEFT-TRIM(cLin) BEGINS "INDEX BLOCK SUMMARY" THEN DO:
            ASSIGN lRecord = FALSE
                   lIndex  = TRUE.
            NEXT.
        END.

        IF  LEFT-TRIM(cLin) BEGINS "DATABASE SUMMARY" THEN DO:
            ASSIGN lRecord = FALSE
                   lIndex  = FALSE.
            NEXT.            
        END.

        IF  lRecord = TRUE 
        AND cLin BEGINS "Totals:" THEN
            ASSIGN lRecord = FALSE.

        IF  lIndex = TRUE 
        AND cLin BEGINS "Totals:" THEN
            ASSIGN lIndex = FALSE.
        
        IF  lRecord = TRUE
        OR  lIndex  = TRUE THEN DO:
            CREATE ttLin.
            ASSIGN ttLin.tcLinh = cLin
                   ttLin.tiLinh = iLinOrg.
            IF lRecord = TRUE THEN
               ASSIGN ttLin.tcCate = "tab".
            IF lIndex = TRUE THEN
               ASSIGN ttLin.tcCate = "ind".
        END.
        
    END.
    INPUT STREAM sDad CLOSE.

    RUN processaProgsTab (hBuffer).

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE processaProgsTab:
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE iLinTot   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE cTab      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cIndex    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cRecord   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cFields   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cFactor   AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cCateg    AS CHARACTER NO-UNDO.
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

        IF  LEFT-TRIM(cLin) BEGINS "_" THEN 
            NEXT.

        IF  ttLin.tcCate = "tab" THEN DO:
            DO  WHILE INDEX(cLin, "  ") > 0:
                ASSIGN cLin = REPLACE(cLin, "  ", " ").
            END.
            ASSIGN cCateg  = "Tab" 
                   cTab    = ENTRY(1, cLin, " ")
                   cRecord = ENTRY(2, cLin, " ")
                   cFactor = ENTRY(9, cLin, " ") 
                   cFields = "" no-error.
            RUN criaLinProgsTab (cCateg, cTab, cIndex, cRecord, cFields, cFactor, cLin, ttLin.tiLinh, hBuffer).
            DELETE ttLin.
            NEXT.
        END.
        IF  ttLin.tcCate = "ind" THEN DO:
            ASSIGN cTab   = TRIM(LEFT-TRIM(cLin))
                   cCateg = "Ind".
            ASSIGN ix = 1.

            FOR EACH bfLin EXCLUSIVE-LOCK
                WHERE bfLin.tiLinh > ttLin.tiLinh:
                ASSIGN cLin3 = bfLin.tcLinh.
                IF  cLin3 BEGINS "_"
                OR  cLin3 BEGINS "  _" 
                OR  cLin3 BEGINS fill(" ", 10) THEN DO:
                    DELETE bfLin.
                    NEXT.
                END.
                
                IF  cLin3 BEGINS " " THEN DO:
                    ASSIGN cLin3 = LEFT-TRIM(cLin3).
                    DO  WHILE INDEX(cLin3, "  ") > 0:
                        ASSIGN cLin3 = REPLACE(cLin3, "  ", " ").
                    END.
                    ASSIGN cIndex  = ENTRY(1, cLin3, " ")
                           cFields = ENTRY(3, cLin3, " ")
                           cFactor = ENTRY(8, cLin3, " ")
                           cRecord = "" no-error.

                    RUN criaLinProgsTab (cCateg, cTab, cIndex, cRecord, cFields, cFactor, cLin, ttLin.tiLinh, hBuffer).
                    DELETE bfLin.
                END.
                ELSE DO:
                    LEAVE.
                END.
            END.
            NEXT.
        END.                           
    END.

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE criaLinProgsTab:
    DEFINE INPUT PARAMETER cCateg  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cTab    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cIndex  AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cRecord AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cFields AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cFactor AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cLin    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE deFactor AS DECIMAL   NO-UNDO.
    
    ASSIGN deFactor = DECIMAL(INTEGER(cFactor) / 10).
    
    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()  = iLin.
    hBuffer:BUFFER-FIELD("tcCate"):BUFFER-VALUE()  = cCateg.
    hBuffer:BUFFER-FIELD("tcTab"):BUFFER-VALUE()   = cTab.
    hBuffer:BUFFER-FIELD("tcInd"):BUFFER-VALUE()   = cIndex.
    hBuffer:BUFFER-FIELD("tiReg"):BUFFER-VALUE()   = INTEGER(cRecord) NO-ERROR.
    hBuffer:BUFFER-FIELD("tiField"):BUFFER-VALUE() = INTEGER(cFields) NO-ERROR.
    hBuffer:BUFFER-FIELD("tiFact"):BUFFER-VALUE()  = deFactor.
    hBuffer:BUFFER-FIELD("tcLinh"):BUFFER-VALUE()  = cLin.

    IF deFactor >= 1.5 THEN DO:
        IF  deFactor < 2.0 THEN DO:
            IF  cCateg = "Tab" THEN 
                hBuffer:BUFFER-FIELD("tcObs"):BUFFER-VALUE() = "Performance prejudicada. Necessita DUMP/LOAD.".
            ELSE
                hBuffer:BUFFER-FIELD("tcObs"):BUFFER-VALUE() = "Necessita reindexacao do indice.".
        END.
        IF  deFactor >= 2.0 THEN DO:
            IF  cCateg = "Tab" THEN 
                hBuffer:BUFFER-FIELD("tcObs"):BUFFER-VALUE() = "Performance prejudicada. Precisa DUMP/LOAD URGENTE.".
            ELSE
                hBuffer:BUFFER-FIELD("tcObs"):BUFFER-VALUE() = "Necessita reindexacao do indice URGENTE.".
        END.
    END.  

    RUN criaCateg ("", cCateg).
END PROCEDURE.

/* fim */
