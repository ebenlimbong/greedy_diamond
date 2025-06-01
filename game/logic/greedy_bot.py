from typing import Tuple, Optional
from game.logic.base import BaseLogic
from game.models import GameObject, Board, Position
from game.util import position_equals


class BotGreedy(BaseLogic):
    def __init__(self):
        self.hitung_macet = 0
        self.posisi_terakhir = None
        self.mode_kumpul = False  # False = cari terdekat dari home, True = cari terdekat dari posisi saat ini
        
    def next_move(self, bot: GameObject, papan: Board) -> Tuple[int, int]:
        posisi_saat_ini = bot.position
        properti = bot.properties
        
        # Deteksi jika bot terjebak
        if self.posisi_terakhir and position_equals(posisi_saat_ini, self.posisi_terakhir):
            self.hitung_macet += 1
        else:
            self.hitung_macet = 0
        self.posisi_terakhir = posisi_saat_ini
        
        # Jika macet lebih dari 3 langkah, coba keluar
        if self.hitung_macet >= 3:
            return self._keluar_dari_macet(posisi_saat_ini, papan)
        
        # Kembali ke home hanya jika tas sudah penuh
        if properti.diamonds >= properti.inventory_size:
            self.mode_kumpul = False  # Reset ke mode pencarian dari home setelah kembali
            return self._bergerak_menuju(posisi_saat_ini, properti.base, papan)
        
        # Tentukan target diamond tergantung mode
        if self.mode_kumpul:
            # Cari diamond terdekat dari posisi sekarang
            target_diamond = self._cari_diamond_terdekat_dari_posisi(papan, properti, posisi_saat_ini)
            if not target_diamond:
                # Tidak ada di sekitar, kembali ke pencarian dari home
                self.mode_kumpul = False
                target_diamond = self._cari_diamond_terdekat_dari_home(papan, properti)
        else:
            # Cari diamond terdekat dari home
            target_diamond = self._cari_diamond_terdekat_dari_home(papan, properti)
            if target_diamond:
                self.mode_kumpul = True  # Setelah menemukan, pindah ke mode pencarian dari posisi
        
        if target_diamond:
            return self._bergerak_menuju(posisi_saat_ini, target_diamond.position, papan)
        
        # Gunakan tombol merah jika diamond sudah habis
        if len(papan.diamonds) == 0:
            self.mode_kumpul = False
            tombol_merah = self._cari_tombol_merah(papan)
            if tombol_merah:
                return self._bergerak_menuju(posisi_saat_ini, tombol_merah.position, papan)
        
        # Kembali ke home jika masih membawa diamond meski sudah tidak ada sisa
        if properti.diamonds > 0:
            self.mode_kumpul = False
            return self._bergerak_menuju(posisi_saat_ini, properti.base, papan)
        
        return (0, 0)
    
    def _cari_diamond_terdekat_dari_home(self, papan: Board, properti) -> Optional[GameObject]:
        """Cari diamond terdekat dari home"""
        if not papan.diamonds:
            return None
        
        home = properti.base
        sisa_ruang = properti.inventory_size - properti.diamonds
        
        terdekat = None
        jarak_terkecil = float('inf')
        
        for diamond in papan.diamonds:
            if sisa_ruang == 1 and self._adalah_diamond_merah(diamond):
                continue
            
            jarak = abs(diamond.position.x - home.x) + abs(diamond.position.y - home.y)
            
            if jarak < jarak_terkecil:
                jarak_terkecil = jarak
                terdekat = diamond
        
        return terdekat
    
    def _cari_diamond_terdekat_dari_posisi(self, papan: Board, properti, posisi: Position) -> Optional[GameObject]:
        """Cari diamond terdekat dari posisi saat ini"""
        if not papan.diamonds:
            return None
        
        sisa_ruang = properti.inventory_size - properti.diamonds
        
        terdekat = None
        jarak_terkecil = float('inf')
        
        for diamond in papan.diamonds:
            if sisa_ruang == 1 and self._adalah_diamond_merah(diamond):
                continue
            
            jarak = abs(diamond.position.x - posisi.x) + abs(diamond.position.y - posisi.y)
            
            if jarak < jarak_terkecil:
                jarak_terkecil = jarak
                terdekat = diamond
        
        return terdekat
    
    def _bergerak_menuju(self, sekarang: Position, tujuan: Position, papan: Board) -> Tuple[int, int]:
        """Bergerak langsung menuju target dengan jalur terpendek"""
        if position_equals(sekarang, tujuan):
            return (0, 0)
        
        dx = tujuan.x - sekarang.x
        dy = tujuan.y - sekarang.y
        
        # Bergerak ke arah yang lebih jauh terlebih dahulu
        if abs(dx) >= abs(dy):
            langkah = (1 if dx > 0 else -1, 0)
            if self._langkah_valid(sekarang, langkah, papan):
                return langkah
            if dy != 0:
                langkah = (0, 1 if dy > 0 else -1)
                if self._langkah_valid(sekarang, langkah, papan):
                    return langkah
        else:
            langkah = (0, 1 if dy > 0 else -1)
            if self._langkah_valid(sekarang, langkah, papan):
                return langkah
            if dx != 0:
                langkah = (1 if dx > 0 else -1, 0)
                if self._langkah_valid(sekarang, langkah, papan):
                    return langkah
        
        # Coba semua arah jika terhalang
        for langkah in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if self._langkah_valid(sekarang, langkah, papan):
                return langkah
        
        return (0, 0)
    
    def _keluar_dari_macet(self, posisi: Position, papan: Board) -> Tuple[int, int]:
        """Berusaha keluar dari posisi macet"""
        for langkah in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if self._langkah_valid(posisi, langkah, papan):
                self.hitung_macet = 0
                return langkah
        return (0, 0)
    
    def _langkah_valid(self, posisi: Position, langkah: Tuple[int, int], papan: Board) -> bool:
        """Cek apakah langkah valid"""
        x_baru = posisi.x + langkah[0]
        y_baru = posisi.y + langkah[1]
        
        if not (0 <= x_baru < papan.width and 0 <= y_baru < papan.height):
            return False
        
        for bot in papan.bots:
            if bot.position.x == x_baru and bot.position.y == y_baru:
                return False
        
        return True
    
    def _adalah_diamond_merah(self, diamond: GameObject) -> bool:
        """Cek apakah diamond merah (bernilai 2 poin)"""
        if diamond.properties and hasattr(diamond.properties, 'points'):
            return diamond.properties.points == 2
        return 'red' in str(diamond.type).lower()
    
    def _cari_tombol_merah(self, papan: Board) -> Optional[GameObject]:
        """Mencari tombol merah di papan"""
        for objek in papan.game_objects:
            if 'button' in objek.type.lower():
                return objek
        return None
