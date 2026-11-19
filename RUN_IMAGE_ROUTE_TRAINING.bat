@echo off
setlocal
cd /d "%~dp0"

rem Edit these values before starting a run.
set MAX_STEPS=1000
set BATCH_SIZE=4
set LATENT_DIM=64
set EMBEDDING_DIM=32
set DEVICE=auto
set OUTPUT_DIR=runs\arabic-contextual-baseline
set EPISODES_DIR=data\contextual_style_episodes
set TARGET_ROOT=data\contextual_glyph_crops
set REFERENCE_ROOT=data\glyph_crops
set RIGHTS_MANIFEST=data\manifests\font_rights.json

echo ============================================================
echo Arabic Font Research - Image-Reference Raster Training
echo ============================================================
echo This starts a real training run. It is NOT a preflight.
echo Steps: %MAX_STEPS%
echo Batch: %BATCH_SIZE%
echo Latent dimension: %LATENT_DIM%
echo Embedding dimension: %EMBEDDING_DIM%
echo Device: %DEVICE%
echo Output: %OUTPUT_DIR%
echo.

if not exist "%EPISODES_DIR%\train.jsonl" (
  echo ERROR: Missing %EPISODES_DIR%\train.jsonl
  echo Download and extract the arabic-contextual-style-episodes artifact.
  goto :failed
)
if not exist "%EPISODES_DIR%\validation.jsonl" (
  echo ERROR: Missing validation.jsonl
  goto :failed
)
if not exist "%EPISODES_DIR%\test.jsonl" (
  echo ERROR: Missing test.jsonl
  goto :failed
)
if not exist "%TARGET_ROOT%\contextual_clusters.jsonl" (
  echo ERROR: Missing contextual target dataset under %TARGET_ROOT%
  echo Extract the arabic-harfbuzz-contextual-clusters artifact there.
  goto :failed
)
if not exist "%REFERENCE_ROOT%\glyph_crops.jsonl" (
  echo ERROR: Missing isolated reference dataset under %REFERENCE_ROOT%
  echo Extract the isolated-arabic-glyph-crops artifact there.
  goto :failed
)
if not exist "%RIGHTS_MANIFEST%" (
  echo ERROR: Missing %RIGHTS_MANIFEST%
  echo Extract the conditional-ofl-font-rights-manifest artifact there.
  goto :failed
)
if not exist "reports\local\machine_preflight.json" (
  echo ERROR: Run START_LOCAL_TRAINING.bat first. Hardware/data preflight is missing.
  goto :failed
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -c "import json,sys; d=json.load(open('reports/local/machine_preflight.json',encoding='utf-8')); sys.exit(0 if d.get('status')=='READY_FOR_EXPERIMENTAL_IMAGE_ROUTE' and d.get('training_allowed') else 1)"
) else (
  python -c "import json,sys; d=json.load(open('reports/local/machine_preflight.json',encoding='utf-8')); sys.exit(0 if d.get('status')=='READY_FOR_EXPERIMENTAL_IMAGE_ROUTE' and d.get('training_allowed') else 1)"
)
if errorlevel 1 (
  echo ERROR: The latest local preflight is not READY. Rerun START_LOCAL_TRAINING.bat and inspect blockers.
  goto :failed
)

echo IMPORTANT LICENSE CONDITION:
echo Generated font files based on these sources must be released under SIL OFL 1.1.
echo The model weights have a separate license decision.
echo.
set /p CONFIRM=Type TRAIN to start the actual training run: 
if /I not "%CONFIRM%"=="TRAIN" (
  echo Cancelled. No training was started.
  goto :done
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m scripts.train_multimodal_glyph --episodes-dir "%EPISODES_DIR%" --target-root "%TARGET_ROOT%" --reference-root "%REFERENCE_ROOT%" --rights-manifest "%RIGHTS_MANIFEST%" --output-dir "%OUTPUT_DIR%" --max-steps %MAX_STEPS% --batch-size %BATCH_SIZE% --latent-dim %LATENT_DIM% --embedding-dim %EMBEDDING_DIM% --device %DEVICE%
) else (
  python -m scripts.train_multimodal_glyph --episodes-dir "%EPISODES_DIR%" --target-root "%TARGET_ROOT%" --reference-root "%REFERENCE_ROOT%" --rights-manifest "%RIGHTS_MANIFEST%" --output-dir "%OUTPUT_DIR%" --max-steps %MAX_STEPS% --batch-size %BATCH_SIZE% --latent-dim %LATENT_DIM% --device %DEVICE%
)

if errorlevel 1 goto :failed
echo.
echo Training command completed. Check %OUTPUT_DIR%\training_summary.json
goto :done

:failed
echo.
echo Training did not start or did not complete successfully.
exit /b 1

:done
echo.
pause
