import jinja2
import json
from pathlib import Path
import xlsxwriter
import csv
from results_type import Results, Result

RESULTS_PATH = Path("RESULTS/results.json")

RESULTS_OUT_MD_PATH = Path("RESULTS/README.md")
RESULTS_OUT_MD_TEMPLATE_PATH = "scripts/RESULTS.md.tpl"

RESULTS_OUT_XLSX_PATH = "RESULTS/results.xlsx"
RESULTS_OUT_CSV_PATH = Path("RESULTS/results.csv")


class ResultLine:
    def __init__(self, r: Result):
        self.result = r

    def md_table_line(self) -> str:
        return (
            "|"
            + "|".join(
                [
                    self.result.vendor.replace("|", r"\|"),
                    self.result.application_id.replace("|", r"\|"),
                    self.result.version.replace("|", r"\|"),
                    ",".join(map(lambda x: x.replace("|", r"\|"), self.result.equiv_releases)),
                    ",".join(map(lambda x: x.replace("|", r"\|"), self.result.doc_type)),
                    ",".join(map(lambda x: x.replace("|", r"\|"), self.result.service)),
                    str(self.result.date).replace("|", r"\|"),
                    self.result.gtw_version.replace("|", r"\|"),
                ]
            )
            + "|"
        )

    def flatten_line(self):
        return [
            self.result.vendor,
            self.result.application_id,
            self.result.version,
            ", ".join(self.result.equiv_releases),
            ",".join(self.result.doc_type),
            ",".join(self.result.service),
            self.result.date,
            self.result.gtw_version,
        ]


def generate_md(md_table_lines: list[str]):
    templateLoader = jinja2.FileSystemLoader(searchpath="./")
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template(RESULTS_OUT_MD_TEMPLATE_PATH)
    outputText = template.render(md_table_lines=md_table_lines)
    RESULTS_OUT_MD_PATH.write_text(outputText, encoding="utf8")


def generate_xlsx(xls_lines: list[list[str]]):
    workbook = xlsxwriter.Workbook(RESULTS_OUT_XLSX_PATH)
    worksheet = workbook.add_worksheet()

    for row_num, row_data in enumerate(xls_lines):
        for col_num, col_data in enumerate(row_data):
            worksheet.write(row_num, col_num, col_data)

    for col in range(len(xls_lines[0])):
        worksheet.set_column(col, col, width=max([len(str(xls_lines[r][col])) for r in range(len(xls_lines))]))

    workbook.close()


def generate_csv(lines: list[list[str]]):
    with RESULTS_OUT_CSV_PATH.open("w", encoding="utf8") as outfile:
        csv_writer = csv.writer(outfile, dialect=csv.excel)
        csv_writer.writerows(lines)


if __name__ == "__main__":
    try:
        with RESULTS_PATH.open("r", encoding="utf8") as results_file:
            data = json.load(results_file)
        results = Results(**data)
        md_lines = []
        lines = []
        lines.append(
            [
                "Fornitore",
                "Applicativo",
                "Versione",
                "Versioni Equivalenti",
                "Tipo Documento",
                "Servizio",
                "Data validazione",
                "Versione Gateway",
            ]
        )
        for result in results.results:
            rl = ResultLine(result)
            md_lines.append(rl.md_table_line())
            lines.append(rl.flatten_line())
        generate_md(md_lines)
        generate_csv(lines)
        generate_xlsx(lines)
    except:
        raise
