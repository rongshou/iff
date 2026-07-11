"""案例数据库操作 —— 封装 case_matcher / case_utils 中的 SQL 查询。"""
import sqlite3
from typing import Optional
from ..core.repository import Repository
from ..core.db_table import TABLE_CASES, TABLE_UNIVERSITIES


class CaseRepository(Repository):
    """案例相关的数据库查询。"""

    def get_major_percentiles(
        self, university: str, major_category: str, tier_key: str
    ) -> Optional[sqlite3.Row]:
        """获取指定院校/专业/层次的分位数数据。"""
        return self.fetch_one(
            """SELECT n, p10, p25, p50, p75
               FROM school_major_gpa_percentiles
               WHERE university = ? AND major_category = ? AND tier = ?""",
            (university, major_category, tier_key),
        )

    def get_major_percentiles_batch(
        self, universities: list[str], major_category: str, tier_key: str
    ) -> dict[str, dict]:
        """批量获取多所院校的专业级 GPA 百分位（消除 N+1）。"""
        if not universities:
            return {}
        ph = ",".join("?" for _ in universities)
        rows = self.fetch_all(
            f"""SELECT university, n, p10, p25, p50, p75
                FROM school_major_gpa_percentiles
                WHERE university IN ({ph}) AND major_category = ? AND tier = ?""",
            (*universities, major_category, tier_key),
        )
        return {r["university"]: dict(r) for r in rows}

    def query_cases(
        self,
        sql: str,
        params: tuple,
    ) -> list[dict]:
        """执行案例查询（SQL 由调用方构建，因为包含动态 WHERE）。"""
        rows = self.fetch_all(sql, params)
        return [dict(r) for r in rows]

    def expand_countries(self) -> list[str]:
        """获取所有有案例的国家列表。"""
        rows = self.fetch_all(
            f"SELECT DISTINCT country FROM {TABLE_CASES} WHERE country IS NOT NULL"
        )
        return [r["country"] for r in rows]

    def fetch_university_requirements(self, uni_ids: tuple) -> dict[int, Optional[str]]:
        """获取指定院校的 GPA 要求。"""
        if not uni_ids:
            return {}
        ph = ",".join("?" for _ in uni_ids)
        rows = self.fetch_all(
            f"SELECT id, gpa_requirement FROM {TABLE_UNIVERSITIES} WHERE id IN ({ph})",
            uni_ids,
        )
        return {r["id"]: r["gpa_requirement"] for r in rows}

    def fetch_ranking_batch(self, id_list: tuple) -> list[dict]:
        """批量获取院校排名数据。"""
        if not id_list:
            return []
        ph = ",".join("?" for _ in id_list)
        rows = self.fetch_all(
            f"SELECT id, qs_rank, usnews_rank, the_rank FROM {TABLE_UNIVERSITIES} WHERE id IN ({ph})",
            id_list,
        )
        return [dict(r) for r in rows]

    def fetch_case_gpa_batch(self, id_list: tuple) -> list[dict]:
        """批量获取案例 GPA 数据（限制行数以控制内存占用）。"""
        if not id_list:
            return []
        ph = ",".join("?" for _ in id_list)
        rows = self.fetch_all(
            f"""SELECT c.university_id, c.gpa_score, c.gpa_format
                FROM {TABLE_CASES} c
                WHERE c.university_id IN ({ph})
                  AND c.gpa_score IS NOT NULL
                  AND c.gpa_format IS NOT NULL
                ORDER BY c.admission_time DESC
                LIMIT 50000""",
            id_list,
        )
        return [dict(r) for r in rows]
