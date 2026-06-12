class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidGPAError(AppError):
    def __init__(self, detail: str):
        super().__init__(f"GPA 数据无效: {detail}", status_code=422)


class InvalidCountryError(AppError):
    def __init__(self, countries: list[str]):
        super().__init__(f"不支持的国家/地区: {countries}", status_code=422)


class NotFoundError(AppError):
    def __init__(self, resource: str):
        super().__init__(f"未找到: {resource}", status_code=404)


class DatabaseError(AppError):
    def __init__(self, detail: str):
        super().__init__(f"数据库错误: {detail}", status_code=500)
