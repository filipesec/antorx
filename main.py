#!/usr/bin/env python3
"""automatiza o formulario de passageiros na interface classica do sisaut/antt"""
from __future__ import annotations

import argparse
import csv
import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import (
    NoAlertPresentException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait

root = Path(__file__).resolve().parent
default_csv = root / "passengers.example.csv"
default_issuer = "SSP"
start_url = "https://appweb1.antt.gov.br/autorizacaoDeViagem/AvPublico/inicial.asp"
form_selector = 'form[name="frmSolicitacao"]'
name_selector = f'{form_selector} input[name="txtPassageiro"]'
situation_selector = f'{form_selector} select[name="cmbSituacaoPassageiro"]'
document_type_selector = f'{form_selector} select[name="cmbTipoDocumento1"]'
document_number_selector = f'{form_selector} input[name="txtIdentidade"]'
issuer_selector = f'{form_selector} input[name="txtOrgao"]'
include_selector = f'{form_selector} input#btnInc[type="image"]'


def digits_only(value: str) -> str:
    """remove a formatacao de um numero de documento sem validar o valor"""
    return re.sub(r"\D", "", value or "")


def read_passengers(csv_path: Path) -> list[dict[str, str]]:
    """le dados de passageiros separados por ponto e virgula e aceita cabecalhos antigos em portugues"""
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV nao encontrado: {csv_path}")

    with csv_path.open("r", newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file, delimiter=";"))

    passengers = []
    for row in rows:
        name = (row.get("name") or row.get("nome") or "").strip()
        raw_document = row.get("document")
        if raw_document is None:
            raw_document = row.get("documento") or row.get("cpf") or ""
        document = digits_only(raw_document)
        original_order = row.get("original_order") or row.get("ordem_original") or ""
        if name:
            passengers.append(
                {"name": name, "document": document, "original_order": original_order}
            )
    return passengers


def has_current_form(driver) -> bool:
    try:
        return bool(driver.find_elements(By.CSS_SELECTOR, name_selector)) and bool(
            driver.find_elements(By.CSS_SELECTOR, include_selector)
        )
    except WebDriverException:
        return False


def search_frames(driver, depth: int = 0, max_depth: int = 5) -> bool:
    """busca quadros internos e mantem o navegador no quadro que contem o formulario"""
    if has_current_form(driver):
        return True
    if depth >= max_depth:
        return False
    try:
        frame_count = len(driver.find_elements(By.CSS_SELECTOR, "iframe, frame"))
    except WebDriverException:
        return False

    for frame_index in range(frame_count):
        try:
            driver.switch_to.frame(frame_index)
            if search_frames(driver, depth + 1, max_depth):
                return True
            driver.switch_to.parent_frame()
        except (WebDriverException, StaleElementReferenceException):
            try:
                driver.switch_to.parent_frame()
            except WebDriverException:
                pass
    return False


def locate_passenger_form(driver, timeout: float = 30) -> bool:
    """localiza o formulario de passageiros em qualquer aba ou quadro aberto"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            for window_handle in list(driver.window_handles):
                try:
                    driver.switch_to.window(window_handle)
                    driver.switch_to.default_content()
                    if search_frames(driver):
                        return True
                except WebDriverException:
                    continue
        except WebDriverException:
            pass
        time.sleep(0.25)
    return False


def accept_alert(driver):
    try:
        alert = driver.switch_to.alert
        alert_text = alert.text
        alert.accept()
        return alert_text
    except NoAlertPresentException:
        return None
    except WebDriverException:
        return None


def passenger_row_visible(driver, name: str) -> bool:
    target_name = name.strip().casefold()
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, "table")
        for table in tables:
            try:
                table_text = (table.text or "").casefold()
                if "ordem" not in table_text or "nome" not in table_text:
                    continue
                for table_row in table.find_elements(By.CSS_SELECTOR, "tr"):
                    if target_name in (table_row.text or "").casefold():
                        return True
            except (WebDriverException, StaleElementReferenceException):
                continue
    except WebDriverException:
        pass
    return False


def current_form_is_cleared(driver) -> bool:
    """verifica se os campos do formulario foram limpos apos o envio"""
    try:
        name_value = (
            driver.find_element(By.CSS_SELECTOR, name_selector).get_attribute("value") or ""
        )
        document_value = driver.find_element(
            By.CSS_SELECTOR, document_number_selector
        ).get_attribute("value") or ""
        issuer_value = (
            driver.find_element(By.CSS_SELECTOR, issuer_selector).get_attribute("value") or ""
        )
        return not name_value.strip() and not document_value.strip() and not issuer_value.strip()
    except (WebDriverException, StaleElementReferenceException):
        return False


def set_element_value(element, value: str) -> None:
    element.clear()
    if value:
        element.send_keys(value)


def fill_current_form(driver, person: dict[str, str]) -> None:
    """preenche os campos usando os seletores do formulario sisaut suportado"""
    wait = WebDriverWait(driver, 20)
    name_element = wait.until(
        lambda current_driver: current_driver.find_element(By.CSS_SELECTOR, name_selector)
    )
    situation_element = wait.until(
        lambda current_driver: current_driver.find_element(By.CSS_SELECTOR, situation_selector)
    )
    document_type_element = wait.until(
        lambda current_driver: current_driver.find_element(By.CSS_SELECTOR, document_type_selector)
    )
    document_number_element = wait.until(
        lambda current_driver: current_driver.find_element(
            By.CSS_SELECTOR, document_number_selector
        )
    )
    issuer_element = wait.until(
        lambda current_driver: current_driver.find_element(By.CSS_SELECTOR, issuer_selector)
    )

    Select(situation_element).select_by_value("1")
    Select(document_type_element).select_by_value("1")
    set_element_value(name_element, person["name"])
    set_element_value(document_number_element, person["document"])
    set_element_value(issuer_element, person.get("issuer", default_issuer))


def submit_and_wait(driver, name: str, timeout: float = 60) -> tuple[bool, str]:
    """envia uma vez e aguarda a resposta sem repetir o clique automaticamente"""
    before_origin = str(driver.execute_script("return String(performance.timeOrigin)"))
    button = WebDriverWait(driver, 15).until(
        lambda current_driver: current_driver.find_element(By.CSS_SELECTOR, include_selector)
    )
    click_error = None
    try:
        button.click()
    except WebDriverException as error:
        click_error = str(error).splitlines()[0]

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        alert_text = accept_alert(driver)
        if alert_text is not None:
            return False, f"O proprio formulario exibiu um aviso: {alert_text}"

        if passenger_row_visible(driver, name):
            return True, "passageiro localizado na tabela"

        try:
            current_origin = str(driver.execute_script("return String(performance.timeOrigin)"))
            ready_state = driver.execute_script("return document.readyState")
            if (
                current_origin != before_origin
                and ready_state == "complete"
                and has_current_form(driver)
            ):
                if passenger_row_visible(driver, name):
                    return True, "passageiro localizado na tabela apos o retorno"
                if current_form_is_cleared(driver):
                    return True, "formulario voltou limpo apos inclusao"
                return False, (
                    "A pagina retornou, mas os campos nao foram limpos e o nome "
                    "nao apareceu na tabela."
                )
        except (WebDriverException, StaleElementReferenceException):
            pass
        time.sleep(0.3)

    error_detail = f" (erro no clique: {click_error})" if click_error else ""
    return False, (
        f"A resposta nao foi detectada apos {int(timeout)} segundos{error_detail}. "
        "Nao cliquei novamente."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Antorx - automatiza o formulario de passageiros SISAUT/ANTT"
    )
    parser.add_argument(
        "--csv",
        default=str(default_csv),
        help="arquivo CSV de passageiros, separado por ponto e virgula",
    )
    parser.add_argument(
        "--issuer",
        default=default_issuer,
        help=(
            'orgao emissor aplicado a todos os registros (padrao: SSP); '
            'use --issuer "" para deixar em branco'
        ),
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="localiza o formulario e imprime os seletores, sem cadastrar passageiros",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser()
    try:
        all_passengers = read_passengers(csv_path)
    except Exception as error:
        print(f"Erro ao ler a lista: {error}")
        return 2

    try:
        is_example = csv_path.resolve() == default_csv.resolve()
    except OSError:
        is_example = False
    if is_example and not args.inspect:
        print("Por seguranca, o CSV de exemplo nao pode ser enviado ao SISAUT.")
        print("Crie um arquivo local como passageiros.csv e execute com --csv passageiros.csv.")
        print("Para verificar somente os seletores, use --inspect.")
        return 2

    ready_passengers = [person for person in all_passengers if person["document"]]
    for person in all_passengers:
        person["issuer"] = args.issuer
    manual_passengers = [person for person in all_passengers if not person["document"]]

    print(f"Passageiros com documento informado: {len(ready_passengers)}")
    print(f"Sem documento informado (preenchimento manual): {len(manual_passengers)}")
    if manual_passengers:
        print(
            "Registros sem documento nao serao enviados automaticamente; "
            "trate-os manualmente apos conferir os dados."
        )

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.page_load_strategy = "none"
    options.add_experimental_option("detach", True)

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
    except WebDriverException as error:
        print("Nao foi possivel iniciar Chrome/Chromium pelo Selenium.")
        print(f"Detalhe: {error}")
        return 2

    finished_ok = False
    try:
        driver.get(start_url)
        print("\nO SISAUT foi aberto no navegador.")
        print("Faca login manualmente e navegue ate a tela Relacao de Passageiros (Passo 2).")
        print("A automacao usara os campos de nome, situacao, documento, orgao emissor e inclusao.")
        input("Quando o formulario estiver aberto, pressione Enter neste terminal...")
        if not locate_passenger_form(driver, timeout=45):
            raise RuntimeError(
                "Nao encontrei o formulario ou o botao de inclusao esperado. "
                "O navegador ficara aberto para inspecao."
            )
        print("Formulario encontrado na aba/frame correto.")

        if args.inspect:
            for selector in (
                name_selector,
                situation_selector,
                document_type_selector,
                document_number_selector,
                issuer_selector,
                include_selector,
            ):
                count = len(driver.find_elements(By.CSS_SELECTOR, selector))
                print(f"{selector}: {count} encontrado(s)")
            input("Inspecao concluida. Pressione Enter para terminar; o navegador ficara aberto.")
            return 0

        confirmation = input(
            f"Vou cadastrar {len(ready_passengers)} passageiros com documento informado, "
            "sem validar o numero. Digite SIM para comecar: "
        ).strip().upper()
        if confirmation != "SIM":
            print("Cancelado; nada foi enviado.")
            return 0

        for index, person in enumerate(ready_passengers, start=1):
            print(
                f"\n[{index}/{len(ready_passengers)}] Processando registro; "
                "dados pessoais ocultos no terminal."
            )
            if not locate_passenger_form(driver, timeout=30):
                raise RuntimeError(
                    "Nao foi possivel localizar o formulario apos a resposta anterior. "
                    "Confira o navegador."
                )

            fill_current_form(driver, person)
            print("Campos preenchidos; nome e documento nao sao exibidos no terminal.")
            success, message = submit_and_wait(driver, person["name"], timeout=60)
            if not success:
                print(f"\nATENCAO: {message}")
                print("O navegador ficara aberto e o script nao repetira o clique automaticamente.")
                print("Confira a tela. Se o passageiro apareceu, nao o cadastre novamente.")
                raise RuntimeError(message)
            print(f"Inclusao confirmada: {message}.")
            time.sleep(0.4)

        finished_ok = True
        print("\nTodos os passageiros com documento informado foram processados.")
        print("Registros sem documento foram deixados para preenchimento manual.")
        input("Pressione Enter para fechar o navegador e terminar...")
        return 0

    except KeyboardInterrupt:
        print("\nInterrompido. O navegador ficara aberto para conferir o estado atual.")
        try:
            input("Pressione Enter para encerrar o script; o navegador continuara aberto...")
        except EOFError:
            pass
        return 130
    except Exception as error:
        print(f"\nERRO: {error}")
        print(
            "O navegador ficara aberto. Confira quais passageiros ja entraram "
            "antes de executar a lista novamente."
        )
        try:
            input("Depois de conferir a tela, pressione Enter para encerrar o script...")
        except EOFError:
            pass
        return 1
    finally:
        if finished_ok:
            try:
                driver.quit()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
