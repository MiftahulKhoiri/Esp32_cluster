"""
update.py
Auto update source code dari GitHub
"""

import subprocess
import os

from tools.logger import get_logger

log = get_logger("AI_SELF_UPDATE")


class SelfUpdater:
    def __init__(self, repo_dir: str, branch: str = "main"):
        self.repo_dir = repo_dir
        self.branch = branch

    def _run(self, cmd):
        return subprocess.check_output(
            cmd,
            cwd=self.repo_dir,
            stderr=subprocess.STDOUT,
            text=True
        ).strip()

    def _is_git_repo(self) -> bool:
        return os.path.isdir(os.path.join(self.repo_dir, ".git"))

    def has_tracked_changes(self) -> bool:
        """
        True jika ada perubahan pada file yang DI-TRACK git
        (file di .gitignore diabaikan)
        """
        status = self._run([
            "git",
            "status",
            "--porcelain",
            "--untracked-files=no"
        ])
        return status != ""

    def get_local_commit(self) -> str:
        return self._run(["git", "rev-parse", "HEAD"])

    def get_remote_commit(self) -> str:
        self._run(["git", "fetch", "origin", self.branch])
        return self._run(["git", "rev-parse", f"origin/{self.branch}"])

    def update_if_needed(self) -> bool:
        """
        Return True jika update terjadi dan aplikasi perlu restart
        """
        try:
            if not self._is_git_repo():
                log.warning("Folder bukan Git repository, skip auto update")
                return False

            # ⛔ HANYA cegah update jika FILE KODE (tracked) berubah
            if self.has_tracked_changes():
                log.warning(
                    "Perubahan kode lokal terdeteksi, skip auto update"
                )
                return False

            local = self.get_local_commit()
            remote = self.get_remote_commit()

            log.info(f"Local commit  : {local[:8]}")
            log.info(f"Remote commit : {remote[:8]}")

            if local == remote:
                log.info("Kode sudah terbaru (skip)")
                return False

            log.warning("Update terdeteksi, menarik kode terbaru...")
            subprocess.run(
                ["git", "pull", "--rebase", "origin", self.branch],
                cwd=self.repo_dir,
                check=True
            )

            log.info("Update selesai, restart aplikasi diperlukan")
            return True

        except Exception as e:
            log.error(f"Gagal auto update: {e}")
            return False