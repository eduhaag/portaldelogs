/************************************************************************************************
** Procedures para Progress Xref
************************************************************************************************/

PROCEDURE criaTTProgsXref:
    DEFINE OUTPUT PARAMETER ttLog   AS HANDLE NO-UNDO.
    DEFINE OUTPUT PARAMETER hLogBuf AS HANDLE NO-UNDO.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    CREATE TEMP-TABLE ttLog.
    /*ttLogTab:ADD-NEW-FIELD("campo","tipo",extent,format,initial,"label").*/
    ttLog:ADD-NEW-FIELD("tiLinh",  "INTE",0,"","","Linha").
    ttLog:ADD-NEW-FIELD("tcProg",  "CHAR",0,"X(30)","","Programa").
    ttLog:ADD-NEW-FIELD("tcTipo",  "CHAR",0,"x(20)","","Tipo").
    ttLog:ADD-NEW-FIELD("tcKey",   "CHAR",0,"x(50)","","Chave").
    ttLog:ADD-NEW-FIELD("tcPar",   "CHAR",0,"x(40)","","Parametros").
    ttLog:ADD-NEW-FIELD("tcRet",   "CHAR",0,"x(40)","","Retorno").
    ttLog:ADD-NEW-FIELD("tlFull",  "LOGI",0,"X/","","Full-Scan").
    ttLog:ADD-NEW-FIELD("tlSeq",   "LOGI",0,"X/","","Sequencia").
    ttLog:ADD-NEW-FIELD("tlGlob",  "LOGI",0,"X/","","Global").
    ttLog:ADD-NEW-FIELD("tlShare", "LOGI",0,"X/","","Shared").
    ttLog:ADD-NEW-FIELD("tlPers",  "LOGI",0,"X/","","Persistente").
    ttLog:ADD-NEW-FIELD("tlTrad",  "LOGI",0,"X/","","Traduzivel").

    /* criacao de indice */
    ttLog:ADD-NEW-INDEX("codigo", NO /* unique*/, YES /* primario */).
    ttLog:ADD-INDEX-FIELD("codigo", "tcProg").
    ttLog:ADD-INDEX-FIELD("codigo", "tcTipo").
    ttLog:ADD-INDEX-FIELD("codigo", "tcKey").
    ttLog:ADD-INDEX-FIELD("codigo", "tiLinh").

    /* prepara a ttLog */
    ttLog:TEMP-TABLE-PREPARE("ttLog").

    /* cria o buffer da TT para alimentar os dados */
    hLogBuf = ttLog:DEFAULT-BUFFER-HANDLE.
END PROCEDURE.

PROCEDURE logProgsXref:
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
                                VIEW-AS RADIO-SET HORIZONTAL 
                                    RADIO-BUTTONS "Tudo", "ALL",    
                                                  "Tabelas", "REFERENCE",
                                                  "Criacao", "CREATE",
                                                  "Leitura", "READ",
                                                  "Atualizacao", "UPDATE",
                                                  "Eliminacao", "DELETE",
                                                  "Acesso", "ACCESS",
                                                  "Includes", "INCLUDE",
                                                  "Funcoes", "FUNCTION",
                                                  "Procedures", "PROCEDURE", 
                                                  "Proc.Externas", "PROC.EXT",
                                                  "Variaveis Globais", "VAR.GLOBAL",
                                                  "Execucao", "RUN",
                                                  "Strings", "STRING".
                                    
    DEFINE FRAME f-log
        rsCatLst   LABEL "Tipo" AT ROW 01.5 COL 3
        cFilter    VIEW-AS FILL-IN SIZE 47 BY 1 NO-LABELS AT ROW 02.5 COL 3
        btFilter   btClear
        btClip     AT ROW 27.5 COL 3 btNotepad btPrint btExit
        WITH ROW 3 SIDE-LABELS THREE-D SIZE 178 BY 28.

    /* cria a temp-table dinamicamente e adiciona os campos*/
    RUN criaTTProgsXref (OUTPUT hTTLog, OUTPUT hBuffer).

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
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tiLinh")).  // 1
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcProg")).  // 2
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcTipo")).  // 3
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcKey")).   // 4
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcPar")).   // 5
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tcRet")).   // 6
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tlFull")).  // 7
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tlSeq")).   // 8
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tlGlob")).  // 9
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tlShare")). // 10
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tlPers")).  // 11
    hBrowse:ADD-LIKE-COLUMN(hBuffer:BUFFER-FIELD("tlTrad")).  // 12

    ON  CHOOSE OF btPrint DO:
        DEFINE VARIABLE cArqPrint AS CHARACTER NO-UNDO.

        ASSIGN rsCatLst.
        ASSIGN cArqPrint = pDir + "/" + ENTRY(1, pArq, ".") + "_" + rsCatLst + ".log".
        OUTPUT TO VALUE(cArqPrint).
        
        /* cabecalho */
        PUT UNFORMATTED "Linha;Programa;Tipo;".
        CASE rsCatLst:
            WHEN "REFERENCE"  OR 
            WHEN "CREATE"     OR
            WHEN "DELETE"     THEN PUT UNFORMATTED "Tabela;".
            WHEN "READ"       THEN PUT UNFORMATTED "Tabela;Full-Scan".
            WHEN "UPDATE"     THEN PUT UNFORMATTED "Chave;Sequencia;Global;Shared".
            WHEN "ACCESS"     THEN PUT UNFORMATTED "Chave;Sequencia;Global;Shared".
            WHEN "INCLUDE"    THEN PUT UNFORMATTED "Include;".
            WHEN "PROCEDURE"  THEN PUT UNFORMATTED "Procedure;Parametros;Retorno".
            WHEN "FUNCTION"   THEN PUT UNFORMATTED "Funcao;Parametros;Retorno".
            WHEN "PROC.EXT"   THEN PUT UNFORMATTED "Procedure Externa;Parametros;Retorno".
            WHEN "VAR.GLOBAL" THEN PUT UNFORMATTED "Variavel Global;".
            WHEN "RUN"        THEN PUT UNFORMATTED "Programa;Persistente".
            WHEN "STRING"     THEN PUT UNFORMATTED "String;Traduzivel".
            OTHERWISE              PUT UNFORMATTED "Chave;Parametros;Retorno;Full-Scan;Sequencia;Global;Shared;Persistente;Traduzivel".
        END CASE.
        PUT UNFORMATTED SKIP.
            
        hQuery:GET-FIRST().
        DO  WHILE NOT hQuery:QUERY-OFF-END:
            PUT UNFORMATTED
                hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcProg"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcTipo"):BUFFER-VALUE() ";"
                hBuffer:BUFFER-FIELD("tcKey"):BUFFER-VALUE()  ";".
            CASE rsCatLst:
                WHEN "READ"       THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlFull"):BUFFER-VALUE() ";". 
                WHEN "ACCESS"     OR 
                WHEN "UPDATE"     THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlSeq"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlGlob"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlShare"):BUFFER-VALUE() ";".
                WHEN "FUNCTION"   OR
                WHEN "PROC.EXT"   OR
                WHEN "PROCEDURE"  THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tcPar"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tcRet"):BUFFER-VALUE() ";".
                WHEN "RUN"        THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlPers"):BUFFER-VALUE() ";".
                WHEN "STRING"     THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlTrad"):BUFFER-VALUE() ";". 
                OTHERWISE              PUT UNFORMATTED hBuffer:BUFFER-FIELD("tcPar"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tcRet"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlFull"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlSeq"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlGlob"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlShare"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlPers"):BUFFER-VALUE() ";"
                                                       hBuffer:BUFFER-FIELD("tlTrad"):BUFFER-VALUE() ";".
            END CASE.

            PUT UNFORMATTED SKIP.
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
        
        ASSIGN cCab = "Linha;Programa;Tipo;".
        CASE rsCatLst:
            WHEN "REFERENCE"  OR 
            WHEN "CREATE"     OR
            WHEN "DELETE"     THEN ASSIGN cCab = cCab + "Tabela;".
            WHEN "READ"       THEN ASSIGN cCab = cCab + "Tabela;Full-Scan".
            WHEN "UPDATE"     THEN ASSIGN cCab = cCab + "Chave;Sequencia;Global;Shared".
            WHEN "ACCESS"     THEN ASSIGN cCab = cCab + "Chave;Sequencia;Global;Shared".
            WHEN "INCLUDE"    THEN ASSIGN cCab = cCab + "Include;".
            WHEN "PROCEDURE"  THEN ASSIGN cCab = cCab + "Procedure;Parametros;Retorno".
            WHEN "FUNCTION"   THEN ASSIGN cCab = cCab + "Funcao;Parametros;Retorno".
            WHEN "PROC.EXT"   THEN ASSIGN cCab = cCab + "Procedure Externa;Parametros;Retorno".
            WHEN "VAR.GLOBAL" THEN ASSIGN cCab = cCab + "Variavel Global;".
            WHEN "RUN"        THEN ASSIGN cCab = cCab + "Programa;Persistente".
            WHEN "STRING"     THEN ASSIGN cCab = cCab + "String;Traduzivel".
            OTHERWISE              ASSIGN cCab = cCab + "Chave;Parametros;Retorno;Full-Scan;Sequencia;Global;Shared;Persistente;Traduzivel".
        END CASE.

        ASSIGN cLin = STRING(hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()) + ";" 
                    + hBuffer:BUFFER-FIELD("tcProg"):BUFFER-VALUE() + ";"
                    + hBuffer:BUFFER-FIELD("tcTipo"):BUFFER-VALUE() + ";"
                    + hBuffer:BUFFER-FIELD("tcKey"):BUFFER-VALUE()  + ";".

        CASE rsCatLst:
            WHEN "READ"       THEN ASSIGN cLin = cLin + string(hBuffer:BUFFER-FIELD("tlFull"):BUFFER-VALUE()). 
            WHEN "ACCESS"     OR 
            WHEN "UPDATE"     THEN ASSIGN cLin = cLin + string(hBuffer:BUFFER-FIELD("tlSeq"):BUFFER-VALUE())  + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlGlob"):BUFFER-VALUE()) + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlShare"):BUFFER-VALUE()).
            WHEN "FUNCTION"   OR
            WHEN "PROC.EXT"   OR
            WHEN "PROCEDURE"  THEN ASSIGN cLin = cLin + hBuffer:BUFFER-FIELD("tcPar"):BUFFER-VALUE() + ";"
                                                      + hBuffer:BUFFER-FIELD("tcRet"):BUFFER-VALUE().
            WHEN "RUN"        THEN ASSIGN cLin = cLin + string(hBuffer:BUFFER-FIELD("tlPers"):BUFFER-VALUE()).
            WHEN "STRING"     THEN ASSIGN cLin = cLin + string(hBuffer:BUFFER-FIELD("tlTrad"):BUFFER-VALUE()). 
            OTHERWISE              ASSIGN cLin = cLin + hBuffer:BUFFER-FIELD("tcPar"):BUFFER-VALUE()           + ";"
                                                      + hBuffer:BUFFER-FIELD("tcRet"):BUFFER-VALUE()           + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlFull"):BUFFER-VALUE())  + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlSeq"):BUFFER-VALUE())   + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlGlob"):BUFFER-VALUE())  + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlShare"):BUFFER-VALUE()) + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlPers"):BUFFER-VALUE())  + ";"
                                                      + string(hBuffer:BUFFER-FIELD("tlTrad"):BUFFER-VALUE()).
        END CASE.
        
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
        PUT UNFORMATTED "Linha;Programa;Tipo;".
        CASE rsCatLst:
            WHEN "REFERENCE"  OR 
            WHEN "CREATE"     OR
            WHEN "DELETE"     THEN PUT UNFORMATTED "Tabela;".
            WHEN "READ"       THEN PUT UNFORMATTED "Tabela;Full-Scan".
            WHEN "UPDATE"     THEN PUT UNFORMATTED "Chave;Sequencia;Global;Shared".
            WHEN "ACCESS"     THEN PUT UNFORMATTED "Chave;Sequencia;Global;Shared".
            WHEN "INCLUDE"    THEN PUT UNFORMATTED "Include;".
            WHEN "PROCEDURE"  THEN PUT UNFORMATTED "Procedure;Parametros;Retorno".
            WHEN "FUNCTION"   THEN PUT UNFORMATTED "Funcao;Parametros;Retorno".
            WHEN "PROC.EXT"   THEN PUT UNFORMATTED "Procedure Externa;Parametros;Retorno".
            WHEN "VAR.GLOBAL" THEN PUT UNFORMATTED "Variavel Global;".
            WHEN "RUN"        THEN PUT UNFORMATTED "Programa;Persistente".
            WHEN "STRING"     THEN PUT UNFORMATTED "String;Traduzivel".
            OTHERWISE              PUT UNFORMATTED "Chave;Parametros;Retorno;Full-Scan;Sequencia;Global;Shared;Persistente;Traduzivel".
        END CASE.
        PUT UNFORMATTED SKIP.
            
        PUT UNFORMATTED
            hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE() ";"
            hBuffer:BUFFER-FIELD("tcProg"):BUFFER-VALUE() ";"
            hBuffer:BUFFER-FIELD("tcTipo"):BUFFER-VALUE() ";"
            hBuffer:BUFFER-FIELD("tcKey"):BUFFER-VALUE()  ";".
        CASE rsCatLst:
            WHEN "READ"       THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlFull"):BUFFER-VALUE()  ";". 
            WHEN "ACCESS"     OR 
            WHEN "UPDATE"     THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlSeq"):BUFFER-VALUE()   ";"
                                                   hBuffer:BUFFER-FIELD("tlGlob"):BUFFER-VALUE()  ";"
                                                   hBuffer:BUFFER-FIELD("tlShare"):BUFFER-VALUE() ";".
            WHEN "FUNCTION"   OR
            WHEN "PROC.EXT"   OR
            WHEN "PROCEDURE"  THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tcPar"):BUFFER-VALUE()   ";"
                                                   hBuffer:BUFFER-FIELD("tcRet"):BUFFER-VALUE()   ";".
            WHEN "RUN"        THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlPers"):BUFFER-VALUE()  ";".
            WHEN "STRING"     THEN PUT UNFORMATTED hBuffer:BUFFER-FIELD("tlTrad"):BUFFER-VALUE()  ";". 
            OTHERWISE              PUT UNFORMATTED hBuffer:BUFFER-FIELD("tcPar"):BUFFER-VALUE()   ";"
                                                   hBuffer:BUFFER-FIELD("tcRet"):BUFFER-VALUE()   ";"
                                                   hBuffer:BUFFER-FIELD("tlFull"):BUFFER-VALUE()  ";"
                                                   hBuffer:BUFFER-FIELD("tlSeq"):BUFFER-VALUE()   ";"
                                                   hBuffer:BUFFER-FIELD("tlGlob"):BUFFER-VALUE()  ";"
                                                   hBuffer:BUFFER-FIELD("tlShare"):BUFFER-VALUE() ";"
                                                   hBuffer:BUFFER-FIELD("tlPers"):BUFFER-VALUE()  ";"
                                                   hBuffer:BUFFER-FIELD("tlTrad"):BUFFER-VALUE()  ";".
        END CASE.
        PUT UNFORMATTED SKIP.
        
        OUTPUT CLOSE.
        OS-COMMAND NO-WAIT VALUE("notepad " + cArqPrint).
    END.
    
    ON  VALUE-CHANGED OF rsCatLst DO:
        ASSIGN rsCatLst. 
        ASSIGN lOrdem = TRUE.

        hBrowse:GET-BROWSE-COLUMN(05):visible = (rsCatLst= "ALL" OR INDEX("PROCEDURE,FUNCTION,PROC.EXT", rsCatLst) > 0).
        hBrowse:GET-BROWSE-COLUMN(06):visible = (rsCatLst= "ALL" OR INDEX("PROCEDURE,FUNCTION,PROC.EXT", rsCatLst) > 0).
        hBrowse:GET-BROWSE-COLUMN(07):visible = (rsCatLst= "ALL" OR rsCatLst = "READ").
        hBrowse:GET-BROWSE-COLUMN(08):visible = (rsCatLst= "ALL" OR INDEX("UPDATE,ACCESS", rsCatLst) > 0).
        hBrowse:GET-BROWSE-COLUMN(09):visible = (rsCatLst= "ALL" OR INDEX("UPDATE,ACCESS", rsCatLst) > 0).
        hBrowse:GET-BROWSE-COLUMN(10):visible = (rsCatLst= "ALL" OR INDEX("UPDATE,ACCESS", rsCatLst) > 0).
        hBrowse:GET-BROWSE-COLUMN(11):visible = (rsCatLst= "ALL" OR rsCatLst = "RUN").
        hBrowse:GET-BROWSE-COLUMN(12):visible = (rsCatLst= "ALL" OR rsCatLst = "STRING").

        APPLY "recall" TO FRAME f-log.
    END.
        
    ON  MOUSE-SELECT-CLICK OF hBrowse DO:
        IF  hBuffer:AVAILABLE
        AND hBrowse:CURRENT-COLUMN <> ? THEN
            APPLY "recall" TO FRAME f-log.
    END.
    
    ON  RECALL OF FRAME f-log DO:
        DEFINE VARIABLE cQuery AS CHARACTER NO-UNDO.
        
        ASSIGN cFilter.
        ASSIGN rsCatLst.
        ASSIGN cChave = "".

        IF  rsCatLst = "ALL" THEN DO:
            IF  cFilter <> "" THEN
                ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcKey matches '*" + cFilter + "*'".
            ELSE
                ASSIGN cQuery = "FOR EACH ttLog".
        END.
        ELSE DO:
            IF  cFilter <> "" THEN
                ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcTipo = '" + rsCatLst + "'" 
                              + " and ttLog.tcKey matches '*" + cFilter + "*'".
            ELSE
                ASSIGN cQuery = "FOR EACH ttLog WHERE ttLog.tcTipo = '" + rsCatLst + "'".
        END.

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

    ON  CHOOSE OF btClear DO:
        ASSIGN cFilter:SCREEN-VALUE = ""
               cChave = "".
        APPLY "value-changed" TO rsCatLst.
    END.
    
    ON  CHOOSE OF btFilter
    OR  RETURN OF cFilter DO:
        ASSIGN cFilter.
        ASSIGN rsCatLst.

        APPLY "value-changed" TO rsCatLst.
    END.
        
    ASSIGN hFrame           = FRAME f-log:Handle
           hBrw             = hBrowse.

    ENABLE ALL WITH FRAME f-log.

    SESSION:SET-WAIT-STATE("general").

    RUN importaProgsXref (pDir, pArq, hBuffer).

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
        DELETE OBJECT hQuery  NO-ERROR.
        DELETE OBJECT hBuffer NO-ERROR.
        DELETE OBJECT hTTLog NO-ERROR.
    END.
END PROCEDURE.

PROCEDURE importaProgsXref:
    DEFINE INPUT PARAMETER cDir    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cArq    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    DEFINE VARIABLE cArq2     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cKey      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cAtr      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cProg1    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cProg2    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cLin      AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cLinha    AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cOper     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cRet0     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE cPar0     AS CHARACTER NO-UNDO.
    DEFINE VARIABLE iLinOrg   AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iFileLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE iProcLen  AS INTEGER   NO-UNDO.
    DEFINE VARIABLE lShare    AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE lSeq      AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE lGlob     AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE lFull     AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE lPers     AS LOGICAL   NO-UNDO.
    DEFINE VARIABLE lTrad     AS LOGICAL   NO-UNDO.

    RUN zeraTT (hBuffer).

    ASSIGN FILE-INFO:FILENAME = cDir + cArq
           iFileLen           = FILE-INFO:FILE-SIZE
           cInfo              = "".

    INPUT STREAM sDad FROM VALUE(cDir + cArq).
    REPEAT:
        IMPORT STREAM sDad UNFORMATTED cLin NO-ERROR.
        IF  ERROR-STATUS:ERROR = TRUE THEN
            LEAVE.

        ASSIGN iLinOrg  = iLinOrg + 1
               iProcLen = iProcLen + length(cLin).

        IF  NUM-ENTRIES(cLin, " ") < 2 THEN
            NEXT.
        ASSIGN cProg1 = REPLACE(ENTRY(1, cLin, " "),"~\","/")
               cProg2 = REPLACE(ENTRY(2, cLin, " "),"~\","/")
               cLinha = ENTRY(3, cLin, " ")
               cOper  = ENTRY(4, cLin, " ").
    
        IF  cOper = "COMPILE" 
        OR  cOper = "CPINTERNAL" 
        OR  cOper = "CPSTREAM" THEN
            NEXT.
    
        ASSIGN cProg1 = ENTRY(NUM-ENTRIES(cProg1, "/") - 1, cProg1, "/") + "/" + ENTRY(NUM-ENTRIES(cProg1, "/"), cProg1, "/").
        ASSIGN cProg2 = ENTRY(NUM-ENTRIES(cProg2, "/") - 1, cProg2, "/") + "/" + ENTRY(NUM-ENTRIES(cProg2, "/"), cProg2, "/").
    
        CASE cOper:
            WHEN "CREATE"    OR
            WHEN "DELETE"    OR
            WHEN "REFERENCE" THEN DO:
                /* criou ou eliminou registro */
                IF  INDEX(cLin, "TEMPTABLE") > 0 THEN
                    ASSIGN cKey = "Temp-Table." + ENTRY(5, cLin, " ").
                ELSE
                    ASSIGN ckey = ENTRY(1, ENTRY(5, cLin, " "), ".") + "." + ENTRY(2, ENTRY(5, cLin, " "), ".").
                //                      Linha,  Oper,   prog,  key, Ret, Par,  full,   seq,  glob, share,  pers,  trad, hBuffer 
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey,  "", "" , FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, hBuffer).
            END.
    
            WHEN "ACCESS" THEN DO:
                /* acessou campos */
                ASSIGN lShare = FALSE
                       lSeq   = FALSE
                       lGlob  = FALSE.
                IF  INDEX(cLin, "ACCESS SHARED") > 0 THEN DO:
                    ASSIGN lShare = TRUE
                           cKey   = ENTRY(6, cLin, " ").
                END.
                ELSE DO:
                    IF  INDEX(cLin, "SEQUENCE") > 0 THEN
                        ASSIGN lSeq = TRUE.
                    ELSE
                        ASSIGN cKey = ENTRY(6, cLin, " ").
                    ASSIGN cKey = ENTRY(5, cLin, " ").
                END.
                hBuffer:FIND-FIRST("WHERE ttLog.tcProg = '" + cProg2 + "'"
                                 + "AND   ttLog.tcTipo = 'VAR.GLOBAL'" 
                                 + "AND   ttLog.tcKey = '" + cKey + "'", NO-LOCK) NO-ERROR.
                IF  hBuffer:AVAILABLE THEN DO:
                    ASSIGN lGlob = TRUE.
                END.
                //                      Linha,  Oper,   prog,  key, Ret, Par,  full,  seq,  glob,  share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey,  "", "" , FALSE, lSeq, lGlob, lShare, FALSE, FALSE, hBuffer).

            END.
    
            WHEN "UPDATE" THEN DO:
                /* alterou campos */
                ASSIGN lShare = FALSE
                       lSeq   = FALSE
                       lGlob  = FALSE.
                IF  INDEX(cLin, "SEQUENCE") > 0 THEN
                    ASSIGN lSeq = TRUE.
                ELSE DO:
                    IF  INDEX(cLin, "SHARED ") > 0 THEN
                    ASSIGN lShare = TRUE
                           cKey   = ENTRY(6, cLin, " ").
                    ELSE DO:
                        IF  INDEX(cLin, "TEMPTABLE") > 0 
                        AND NUM-ENTRIES(ENTRY(5, cLin, " "), ".") = 1 THEN
                            ASSIGN cKey  = "Temp-Table." + ENTRY(5, cLin, " ").
                        ELSE
                            ASSIGN cKey = ENTRY(5, cLin, " ") no-error.
                    END.
                END.
                hBuffer:FIND-FIRST("WHERE ttLog.tcProg = '" + cProg2 + "'"
                                 + "AND   ttLog.tcTipo = 'VAR.GLOBAL'" 
                                 + "AND   ttLog.tcKey = '" + cKey + "'", NO-LOCK) NO-ERROR.
                IF  hBuffer:AVAILABLE THEN DO:
                    ASSIGN lGlob = TRUE.
                END.
                //                      Linha,  Oper,   prog,  key, Ret, Par,  full,  seq,  glob,  share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey,  "", "" , FALSE, lSeq, lGlob, lShare, FALSE, FALSE, hBuffer).
            END.
    
            WHEN "SEARCH" THEN DO:
                ASSIGN lFull = FALSE.
                /* fez leitura em tabela ou tt */
                IF  INDEX(cLin, "TEMPTABLE") > 0 THEN
                    ASSIGN cKey = "Temp-Table." + ENTRY(5, cLin, " ") + '.' + ENTRY(6, cLin, " ").
                ELSE
                    ASSIGN cKey = ENTRY(5, cLin, " ") + '.' + ENTRY(6, cLin, " ") no-error.
                IF  INDEX(cLin, "WHOLE-INDEX") > 0 THEN
                    ASSIGN lFull = TRUE.
                //                      Linha,   Oper,   prog,  key, Ret, Par,  full,  seq,  glob,  share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, "READ", cProg2, cKey,  "", "" , lFull, FALSE, FALSE, FALSE, FALSE, FALSE, hBuffer).
            END.
            
            WHEN "INCLUDE" THEN DO:
                /* include embutida */
                ASSIGN cKey = REPLACE(ENTRY(5, cLin, " "),"~"","").
                //                     Linha,   Oper,   prog,  key, Ret, Par,  full,  seq,  glob,  share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey,  "", "" , FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, hBuffer).
            END.
            
            WHEN "PROCEDURE" THEN DO:
                /* procedures */
                ASSIGN cKey  = ENTRY(1, ENTRY(5, cLin, " "))
                       cRet0 = ""
                       cPar0 = SUBSTR(cLin, INDEX(cLin, "PROCEDURE ") + 12 + LENGTH(cKey), LENGTH(cLin)).
                //                      Linha,  Oper,   prog,  key,   Ret,   Par,  full,   seq,  glob, share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey, cRet0, cPar0, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, hBuffer).
            END.
    
            WHEN "FUNCTION" THEN DO:
                /* funcoes */
                ASSIGN cKey  = ENTRY(1, ENTRY(5, cLin, " "))
                       cRet0 = ENTRY(2, ENTRY(5, cLin, " "))
                       cPar0 = SUBSTR(cLin, INDEX(cLin, "FUNCTION ") + 11 + LENGTH(cKey) + LENGTH(cRet0), LENGTH(cLin)).
                //                     Linha,   Oper,   prog,  key,   Ret,   Par,  full,   seq,  glob, share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey, cRet0, cPar0, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, hBuffer).
            END.
    
            WHEN "EXTERN" THEN DO:
                /* procedures externas */
                ASSIGN cKey  = ENTRY(1, ENTRY(5, cLin, " "))
                       cRet0 = ENTRY(2, ENTRY(5, cLin, " "))
                       cPar0 = SUBSTR(cLin, INDEX(cLin, "EXTERN ") + 9 + LENGTH(cKey) + LENGTH(cRet0), LENGTH(cLin)).
                //                      Linha,       Oper,   prog,  key,   Ret,   Par,  full,   seq, glob,  share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, "PROC.EXT", cProg2, cKey, cRet0, cPar0, FALSE, FALSE, FALSE, FALSE, FALSE, FALSE, hBuffer).
            END.
    
            WHEN "GLOBAL-VARIABLE" THEN DO:
                /* variaveis globais */
                ASSIGN cKey = ENTRY(5, cLin, " ").
                //                      Linha,         Oper,   prog,  key, Ret, Par,  full,   seq, glob, share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, "VAR.GLOBAL", cProg2, cKey,  '',  '', FALSE, FALSE, TRUE, FALSE, FALSE, FALSE, hBuffer).
            END.
            
            WHEN "RUN" THEN DO:
                /* execucao de programas ou procedures */
                ASSIGN cKey  = REPLACE(ENTRY(5, cLin, " "),"~"","")
                       lPers = (INDEX(cLin, "PERSISTENT") > 0).
                //                      Linha,  Oper,   prog,  key, Ret, Par,  full,   seq,  glob, share,  pers,  trad, hBuffer 
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey,  '',  '', FALSE, FALSE, FALSE, FALSE, lPers, FALSE, hBuffer).
            END.

            WHEN "STRING" THEN DO:
                /* execucao de programas ou procedures */
                ASSIGN cKey  = REPLACE(ENTRY(5, cLin, " "),"~"","")
                       lTrad = (INDEX(cLin, "UNTRANSLATABLE") = 0).
                //                      Linha,  Oper,   prog,  key, Ret, Par,  full,   seq,  glob, share,  pers,  trad, hBuffer
                RUN criaLinProgsXref (iLinOrg, cOper, cProg2, cKey,  '',  '', FALSE, FALSE, FALSE, FALSE, FALSE, lTrad, hBuffer).
            END.
        END.
        IF  cProg1 = cProg2 THEN
            ASSIGN cProg2 = "".

        IF  (iLinOrg MOD 1000) = 0 THEN DO:
            PROCESS EVENTS.
            PUBLISH "showMessage" FROM THIS-PROCEDURE ("Importando " + STRING(iProcLen, "zzz,zzz,zzz,zzz,zz9") + " de " + STRING(iFilelen, "zzz,zzz,zzz,zzz,zz9") + " bytes.").
        END.
    END.

    INPUT STREAM sDad CLOSE.

    HIDE MESSAGE NO-PAUSE.
END PROCEDURE.

PROCEDURE criaLinProgsXref:
    DEFINE INPUT PARAMETER iLin    AS INTEGER   NO-UNDO.
    DEFINE INPUT PARAMETER cTipo   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cProg   AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cKey    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cRet    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER cPar    AS CHARACTER NO-UNDO.
    DEFINE INPUT PARAMETER lFull   AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lSeq    AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lGlob   AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lShare  AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lPers   AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER lTrad   AS LOGICAL   NO-UNDO.
    DEFINE INPUT PARAMETER hBuffer AS HANDLE    NO-UNDO.

    hBuffer:FIND-FIRST("WHERE ttLog.tcProg = '" + cProg + "'"
                     + "AND   ttLog.tcTipo = '" + cTipo + "'" 
                     + "AND   ttLog.tcKey  = '" + cKey  + "'", NO-LOCK) NO-ERROR.
    IF  hBuffer:AVAILABLE THEN DO:
        RETURN.
    END.
    
    /* cria registro */
    hBuffer:BUFFER-CREATE.
    hBuffer:BUFFER-FIELD("tiLinh"):BUFFER-VALUE()  = iLin.
    hBuffer:BUFFER-FIELD("tcProg"):BUFFER-VALUE()  = cProg.
    hBuffer:BUFFER-FIELD("tcTipo"):BUFFER-VALUE()  = cTipo.
    hBuffer:BUFFER-FIELD("tcKey"):BUFFER-VALUE()   = cKey.
    hBuffer:BUFFER-FIELD("tcPar"):BUFFER-VALUE()   = cPar.
    hBuffer:BUFFER-FIELD("tcRet"):BUFFER-VALUE()   = cRet.
    hBuffer:BUFFER-FIELD("tlFull"):BUFFER-VALUE()  = lFull.
    hBuffer:BUFFER-FIELD("tlSeq"):BUFFER-VALUE()   = lSeq.
    hBuffer:BUFFER-FIELD("tlGlob"):BUFFER-VALUE()  = lGlob.
    hBuffer:BUFFER-FIELD("tlShare"):BUFFER-VALUE() = lShare.
    hBuffer:BUFFER-FIELD("tlPers"):BUFFER-VALUE()  = lPers.
    hBuffer:BUFFER-FIELD("tlTrad"):BUFFER-VALUE()  = lTrad.
END PROCEDURE.

/* fim */
