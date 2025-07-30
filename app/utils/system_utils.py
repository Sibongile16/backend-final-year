def determine_system_status(cpu: float, memory: float) -> str:
    if cpu >= 90 or memory >= 90:
        return "critical"
    elif cpu >= 70 or memory >= 75:
        return "warning"
    return "healthy"