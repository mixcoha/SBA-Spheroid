import os
import logging

class LoggerHelper:
    @staticmethod
    def initialize_logger(output_dir=None, filename="cambios_simulacion.log", level=logging.INFO):
        """
        Inicializa el logger si no está configurado aún.
        """
        if not logging.getLogger().hasHandlers():
            if output_dir is None:
                output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
                
            os.makedirs(output_dir, exist_ok=True)
            log_path = os.path.join(output_dir, filename)
            
            # Configurar el logger para que escriba tanto en archivo como en consola
            logger = logging.getLogger()
            logger.setLevel(level)
            
            # Handler para archivo
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            logger.addHandler(file_handler)
            
            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            logger.addHandler(console_handler)
            
            logging.info(f"✅ Logger inicializado en {log_path}")
            logging.info(f"✅ Carpeta de salida: {output_dir}")
        else:
            logging.debug("Logger ya estaba configurado, no se reconfiguró.") 