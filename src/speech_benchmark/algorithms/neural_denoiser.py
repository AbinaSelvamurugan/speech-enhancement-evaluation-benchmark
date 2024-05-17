"""Optional integration status only; never impersonates a pretrained neural model."""


def availability() -> tuple[bool, str]:
    return False, "No pretrained model, checkpoint, or runtime configured; no neural outputs produced."
