import json
import re
from io import StringIO
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from . import chatbot
from .models import (
    ChatbotSettings, ChatKnowledge, ChatLog, Certification, Profile, Project,
    SiteText, UniverseBody,
)
from .templatetags.portfolio_tags import bracket_bold

PORTFOLIO = Path(__file__).resolve().parent


def seed(*args):
    call_command("seed_portfolio", *args, stdout=StringIO())


class SeedTests(TestCase):
    def test_seed_est_idempotent_et_complet(self):
        seed()
        n_texts, n_projects = SiteText.objects.count(), Project.objects.count()
        seed()
        self.assertEqual(SiteText.objects.count(), n_texts)
        self.assertEqual(Project.objects.count(), n_projects)
        self.assertTrue(ChatbotSettings.objects.exists())
        self.assertGreaterEqual(ChatKnowledge.objects.count(), 5)

    def test_seed_ne_ecrase_pas_les_modifications_de_l_admin(self):
        seed()
        Project.objects.filter(order=1).update(title="TITRE MODIFIÉ DANS L'ADMIN")
        SiteText.objects.filter(key="home_greet").update(value="Salut, moi c'est")
        Profile.objects.update(role="Rôle modifié")
        ChatbotSettings.objects.update(instructions="Mes instructions perso")
        ChatKnowledge.objects.all().delete()
        ChatKnowledge.objects.create(title="Mon info", content="x")
        seed()
        self.assertEqual(Project.objects.get(order=1).title, "TITRE MODIFIÉ DANS L'ADMIN")
        self.assertEqual(SiteText.objects.get(key="home_greet").value, "Salut, moi c'est")
        self.assertEqual(Profile.get().role, "Rôle modifié")
        self.assertEqual(ChatbotSettings.get().instructions, "Mes instructions perso")
        self.assertEqual(ChatKnowledge.objects.count(), 1)  # pas de re-création

    def test_seed_reset_reecrit_le_contenu(self):
        seed()
        SiteText.objects.filter(key="home_greet").update(value="Autre")
        seed("--reset")
        self.assertEqual(SiteText.objects.get(key="home_greet").value, "Bonjour, je suis")

    def test_textes_obsoletes_retires(self):
        seed()
        SiteText.objects.create(key="scroll_cue", label="x", value="x", group="accueil")
        seed()
        self.assertFalse(SiteText.objects.filter(key="scroll_cue").exists())

    def test_ancienne_connaissance_gemini_est_migree_sans_ecraser_le_reste(self):
        ChatKnowledge.objects.create(
            title="Ce portfolio", kind="info",
            content="Cet assistant utilise l'API Gemini de Google. Détail conservé.",
        )
        seed()
        knowledge = ChatKnowledge.objects.get(title="Ce portfolio")
        self.assertEqual(
            knowledge.content,
            "Cet assistant utilise l'API OpenRouter. Détail conservé.",
        )


class EditableContentTests(TestCase):
    """Garantit que chaque texte affiché par le site est modifiable dans l'admin."""

    def setUp(self):
        seed()

    def test_toutes_les_cles_de_texte_utilisees_existent_dans_l_admin(self):
        used = set()
        for f in (PORTFOLIO / "templates" / "portfolio").glob("*.html"):
            used |= set(re.findall(r"txt\.([a-z0-9_]+)", f.read_text(encoding="utf-8")))
        used |= set(re.findall(r'\bt\("([a-z0-9_]+)"', (PORTFOLIO / "views.py").read_text(encoding="utf-8")))
        known = set(SiteText.objects.values_list("key", flat=True))
        self.assertEqual(sorted(used - known), [], "Textes affichés mais absents de l'admin")

    def test_chaque_texte_a_un_groupe_valide_donc_une_section_admin(self):
        groups = {g for g, _ in SiteText.GROUP_CHOICES}
        for t in SiteText.objects.all():
            self.assertIn(t.group, groups, t.key)

    def test_modifier_un_texte_change_la_page(self):
        SiteText.objects.filter(key="home_greet").update(value="Coucou, je suis")
        SiteText.objects.filter(key="hs_toast_warp_title").update(value="PASSAGE OK")
        html = Client().get("/").content.decode()
        self.assertIn("Coucou, je suis", html)
        self.assertIn("PASSAGE OK", html)  # message du JS, lu dans le JSON de l'univers 3D

    def test_video_et_seo_editables(self):
        SiteText.objects.filter(key="home_video_url").update(value="https://exemple.test/v.webm")
        SiteText.objects.filter(key="seo_title").update(value="Mon titre SEO")
        html = Client().get("/").content.decode()
        self.assertIn("https://exemple.test/v.webm", html)
        self.assertIn("<title>Mon titre SEO</title>", html)

    def test_commandes_3d_editables_et_echappees(self):
        SiteText.objects.filter(key="hs_cmds_pc_body").update(value="[A] test <script>x</script>")
        html = Client().get("/").content.decode()
        self.assertIn("<b>[A]</b>", html)
        self.assertNotIn("<script>x</script>", html)

    def test_filtre_bracket_bold(self):
        self.assertEqual(bracket_bold("[X] y\nz"), "<b>[X]</b> y<br>z")
        self.assertEqual(bracket_bold("a\\nb"), "a<br>b")
        self.assertNotIn("<i>", bracket_bold("<i>[X]</i>"))

    def test_photo_et_certificat_televerses_remplacent_les_fichiers_statiques(self):
        p = Profile.get()
        self.assertTrue(p.photo_full_url.endswith("avatar_full.webp"))
        c = Certification.objects.first()
        self.assertIn("_full.webp", c.image_full_url)
        c.image.name = "certs/nouveau.png"
        self.assertEqual(c.image_full_url, "/media/certs/nouveau.png")


class PageTests(TestCase):
    def setUp(self):
        seed()

    def test_accueil_contient_le_widget_et_les_donnees_3d(self):
        html = Client().get("/").content.decode()
        self.assertIn('id="chatbot"', html)
        self.assertIn('id="chatbot-config"', html)
        self.assertIn("chatbot.js", html)
        self.assertIn("chatbot.css", html)
        self.assertIn('id="hs-data"', html)

    def test_la_cle_api_n_est_jamais_dans_la_page(self):
        with override_settings(OPENROUTER_API_KEY="SECRET-KEY-123"):
            html = Client().get("/").content.decode()
        self.assertNotIn("SECRET-KEY-123", html)

    def test_widget_retire_si_desactive(self):
        ChatbotSettings.objects.update(enabled=False)
        html = Client().get("/").content.decode()
        self.assertNotIn('id="chatbot"', html)

    def test_donnees_3d_contiennent_les_projets_avec_description(self):
        html = Client().get("/").content.decode()
        raw = re.search(r'<script id="hs-data" type="application/json">(.*?)</script>', html, re.S).group(1)
        data = json.loads(raw)
        self.assertEqual(len(data["projects"]), Project.objects.count())
        self.assertTrue(all(p["desc"] for p in data["projects"]))
        self.assertIn("warpTitle", data["ui"])


class PromptTests(TestCase):
    def setUp(self):
        seed()

    def test_le_prompt_contient_regles_site_et_connaissances(self):
        ChatKnowledge.objects.create(title="Info secrète X", content="Nick adore le café noir.", order=99)
        ChatbotSettings.objects.update(instructions="Toujours terminer par un emoji fusée.")
        prompt = chatbot.build_system_prompt()
        self.assertIn("valoriser", prompt.lower())          # rôle principal
        self.assertIn("IA conversationnelle", prompt)        # généraliste
        self.assertIn("N'invente jamais", prompt)            # honnêteté
        self.assertIn("Toujours terminer par un emoji fusée.", prompt)
        self.assertIn("Nick adore le café noir.", prompt)
        self.assertIn(Project.objects.first().title, prompt)  # fiche issue du site
        self.assertIn(Certification.objects.first().title, prompt)
        self.assertIn("nickkakaye4@gmail.com", prompt)

    def test_connaissance_inactive_exclue(self):
        ChatKnowledge.objects.create(title="Cachée", content="INFO-DESACTIVEE", active=False)
        self.assertNotIn("INFO-DESACTIVEE", chatbot.build_system_prompt())

    def test_le_contenu_du_site_est_relu_a_chaque_fois(self):
        Project.objects.filter(order=1).update(title="PROJET-FRAIS-123")
        self.assertIn("PROJET-FRAIS-123", chatbot.build_system_prompt())

    def test_le_prompt_ne_contient_jamais_la_cle(self):
        with override_settings(OPENROUTER_API_KEY="SECRET-KEY-123"):
            self.assertNotIn("SECRET-KEY-123", chatbot.build_system_prompt())


@override_settings(OPENROUTER_API_KEY="test-key", GROQ_API_KEY="")
class AIProviderClientTests(TestCase):
    def setUp(self):
        seed()
        chatbot._models_cache.update(models=[], at=0.0)
        chatbot._groq_models_cache.update(models=[], at=0.0)
        self.cfg = ChatbotSettings.get()

    @staticmethod
    def _catalog(*models):
        return {"data": [{"id": model} for model in models]}

    def test_requete_http_envoie_la_cle_en_bearer(self):
        response = mock.MagicMock()
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = b"{}"
        with mock.patch("portfolio.chatbot.urllib.request.urlopen", return_value=response) as urlopen:
            for url in (chatbot.OPENROUTER_MODELS_URL, chatbot.GROQ_MODELS_URL):
                self.assertEqual(chatbot._http("GET", url, "unit-test-key"), (200, {}))
                request = urlopen.call_args.args[0]
                self.assertEqual(request.get_header("Authorization"), "Bearer unit-test-key")

    def test_le_catalogue_ne_reste_que_sur_les_identifiants_gratuits(self):
        with mock.patch.object(
                chatbot, "_http",
                return_value=(200, self._catalog("provider/paid-model", "provider/free-model:free"))):
            self.assertEqual(chatbot.available_free_models("K"), ["provider/free-model:free"])

    def test_appel_nominal_avec_detection_automatique(self):
        calls = []

        def fake(method, url, key, body=None):
            calls.append((method, url, key, body))
            if method == "GET":
                return 200, self._catalog("google/gemma-4-31b-it:free")
            return 200, {"choices": [{"message": {"content": "Salut"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            text, model = chatbot.ask_assistant(
                self.cfg, "SYS", [{"role": "user", "text": "a"},
                                  {"role": "assistant", "text": "b"}], "c")
        self.assertEqual((text, model), ("Salut", "openrouter:google/gemma-4-31b-it:free"))
        method, url, key, body = calls[1]
        self.assertEqual((method, url), ("POST", chatbot.OPENROUTER_URL))
        self.assertEqual(key, "test-key")
        self.assertEqual(body["messages"][0], {"role": "system", "content": "SYS"})
        self.assertEqual([item["role"] for item in body["messages"]], ["system", "user", "assistant", "user"])
        self.assertEqual(body["messages"][-1]["content"], "c")

    def test_modele_indisponible_bascule_vers_le_suivant(self):
        ChatbotSettings.objects.update(model_name="ancien/modele:free")
        cfg = ChatbotSettings.get()
        seen = []

        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, self._catalog("provider/model-a:free", "provider/model-b:free")
            seen.append(body["model"])
            if body["model"] == "ancien/modele:free":
                return 404, {"error": {"message": "model not found"}}
            return 200, {"choices": [{"message": {"content": "OK fallback"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            text, model = chatbot.ask_assistant(cfg, "S", [], "q")
        self.assertEqual((text, model), ("OK fallback", "openrouter:provider/model-a:free"))
        self.assertEqual(len(seen), 2)

    def test_quota_ou_surcharge_bascule_vers_un_modele(self):
        calls = []

        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, self._catalog("provider/model-a:free", "provider/model-b:free")
            calls.append(body["model"])
            if len(calls) == 1:
                return 429, {"error": {"message": "rate limit"}}
            return 200, {"choices": [{"message": {"content": "Réponse"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            text, model = chatbot.ask_assistant(self.cfg, "S", [], "q")
        self.assertEqual((text, model), ("Réponse", "openrouter:provider/model-b:free"))
        self.assertEqual(calls, ["provider/model-a:free", "provider/model-b:free"])

    def test_bascule_au_dela_des_trois_premiers_modeles_limites(self):
        calls = []
        catalog = self._catalog(*(f"provider/model-{i}:free" for i in range(1, 7)))

        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, catalog
            calls.append(body["model"])
            if len(calls) < 5:
                return 429, {"error": {"message": "Provider returned error"}}
            return 200, {"choices": [{"message": {"content": "Modèle de secours"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            reply, model = chatbot.ask_assistant(self.cfg, "S", [], "q")
        self.assertEqual((reply, model), ("Modèle de secours", "openrouter:provider/model-5:free"))
        self.assertEqual(calls, [f"provider/model-{i}:free" for i in range(1, 6)])

    @override_settings(OPENROUTER_API_KEY="", GROQ_API_KEY="test-groq-key")
    def test_groq_est_utilise_seul_si_seule_sa_cle_est_configuree(self):
        calls = []

        def fake(method, url, key, body=None):
            calls.append((method, url, key, body))
            if method == "GET":
                return 200, self._catalog(*chatbot.GROQ_FREE_MODELS_PRIORITY)
            return 200, {"choices": [{"message": {"content": "Salut depuis Groq"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            reply, model = chatbot.ask_assistant(self.cfg, "SYS", [], "Bonjour")
        self.assertEqual((reply, model), ("Salut depuis Groq", "groq:openai/gpt-oss-20b"))
        self.assertEqual(calls[0][1], chatbot.GROQ_MODELS_URL)
        self.assertEqual(calls[1][1], chatbot.GROQ_URL)
        self.assertEqual(calls[1][2], "test-groq-key")

    @override_settings(OPENROUTER_API_KEY="test-openrouter-key", GROQ_API_KEY="test-groq-key")
    def test_dix_essais_alternent_entre_les_deux_fournisseurs(self):
        attempted = []

        def fake(method, url, key, body=None):
            if method == "GET":
                if url == chatbot.OPENROUTER_MODELS_URL:
                    return 200, self._catalog(*(f"openrouter/model-{i}:free" for i in range(1, 12)))
                return 200, self._catalog(*chatbot.GROQ_FREE_MODELS_PRIORITY)
            provider = "openrouter" if url == chatbot.OPENROUTER_URL else "groq"
            attempted.append((provider, body["model"]))
            if len(attempted) < 10:
                return 429, {"error": {"message": "rate limit"}}
            return 200, {"choices": [{"message": {"content": "Réponse au dixième essai"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            reply, model = chatbot.ask_assistant(self.cfg, "SYS", [], "Bonjour")
        self.assertEqual(reply, "Réponse au dixième essai")
        self.assertEqual(model, "groq:meta-llama/llama-4-scout-17b-16e-instruct")
        self.assertEqual(len(attempted), chatbot.MAX_MODEL_ATTEMPTS)
        self.assertEqual([provider for provider, _ in attempted], ["openrouter", "groq"] * 5)

    @override_settings(OPENROUTER_API_KEY="bad-openrouter-key", GROQ_API_KEY="test-groq-key")
    def test_cle_openrouter_invalide_passe_a_groq_sans_reessais_inutiles(self):
        attempted = []

        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, self._catalog(
                    "openrouter/model-a:free", *chatbot.GROQ_FREE_MODELS_PRIORITY)
            attempted.append(url)
            if url == chatbot.OPENROUTER_URL:
                return 401, {"error": {"message": "invalid API key"}}
            return 200, {"choices": [{"message": {"content": "Groq répond"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            reply, model = chatbot.ask_assistant(self.cfg, "SYS", [], "Bonjour")
        self.assertEqual((reply, model), ("Groq répond", "groq:openai/gpt-oss-20b"))
        self.assertEqual(attempted, [chatbot.OPENROUTER_URL, chatbot.GROQ_URL])

    @override_settings(OPENROUTER_API_KEY="", GROQ_API_KEY="test-groq-key")
    def test_catalogue_groq_filtre_les_modeles_hors_liste_gratuite(self):
        catalog = self._catalog("paid/model", *chatbot.GROQ_FREE_MODELS_PRIORITY)
        with mock.patch.object(chatbot, "_http", return_value=(200, catalog)):
            models = chatbot.available_free_models("test-groq-key", "groq")
        self.assertEqual(models, chatbot.GROQ_FREE_MODELS_PRIORITY)

    def test_cle_invalide_ne_reessaie_pas_sur_d_autres_modeles(self):
        calls = []

        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, self._catalog("provider/model-a:free", "provider/model-b:free")
            calls.append(body["model"])
            return 401, {"error": {"message": "invalid API key"}}

        with mock.patch.object(chatbot, "_http", fake):
            with self.assertRaises(chatbot.AIProviderError) as cm:
                chatbot.ask_assistant(self.cfg, "S", [], "q")
        self.assertEqual(cm.exception.kind, "config")
        self.assertEqual(len(calls), 1)

    def test_modele_non_gratuit_refuse(self):
        ChatbotSettings.objects.update(model_name="provider/model")
        with self.assertRaises(chatbot.AIProviderError) as cm:
            chatbot.ask_assistant(ChatbotSettings.get(), "S", [], "q")
        self.assertEqual(cm.exception.kind, "config")

    def test_reponse_vide_est_classee(self):
        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, self._catalog("provider/model-a:free")
            return 200, {"choices": [{"message": {"content": ""}}]}

        with mock.patch.object(chatbot, "_http", fake):
            with self.assertRaises(chatbot.AIProviderError) as cm:
                chatbot.ask_assistant(self.cfg, "S", [], "q")
        self.assertEqual(cm.exception.kind, "empty")

    def test_sans_cle_erreur_de_configuration(self):
        with override_settings(OPENROUTER_API_KEY="", GROQ_API_KEY=""):
            with self.assertRaises(chatbot.AIProviderError) as cm:
                chatbot.ask_assistant(self.cfg, "S", [], "q")
        self.assertEqual(cm.exception.kind, "config")

    def test_historique_nettoye(self):
        raw = [{"role": "assistant", "text": "orphelin"}, {"role": "user", "text": "q1"},
               {"role": "assistant", "text": "r1"}, "pas un dict", {"role": "user", "text": "  "},
               {"role": "system", "text": "r2"}, {"role": "user", "text": "x" * 9000}]
        out = chatbot.clean_history(raw, self.cfg)
        self.assertEqual(out[0], {"role": "user", "text": "q1"})
        self.assertEqual([m["role"] for m in out], ["user", "assistant", "assistant", "user"])
        self.assertEqual(len(out[-1]["text"]), 3000)
        self.assertEqual(chatbot.clean_history("n'importe quoi", self.cfg), [])


@override_settings(OPENROUTER_API_KEY="test-key", GROQ_API_KEY="")
class ChatApiTests(TestCase):
    URL = "/api/chat/"

    def setUp(self):
        seed()
        self.client = Client()

    def post(self, payload, **extra):
        return self.client.post(self.URL, json.dumps(payload), content_type="application/json", **extra)

    def test_get_interdit(self):
        self.assertEqual(self.client.get(self.URL).status_code, 405)

    def test_csrf_obligatoire(self):
        c = Client(enforce_csrf_checks=True)
        r = c.post(self.URL, json.dumps({"message": "hi"}), content_type="application/json")
        self.assertEqual(r.status_code, 403)

    def test_csrf_ok_avec_jeton_de_la_page(self):
        c = Client(enforce_csrf_checks=True)
        html = c.get("/").content.decode()
        token = re.search(r'id="chatbot" class="cb" data-csrf="([^"]+)"', html).group(1)
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("Salut !", "m")):
            r = c.post(self.URL, json.dumps({"message": "hi"}), content_type="application/json",
                       HTTP_X_CSRFTOKEN=token)
        self.assertEqual(r.status_code, 200, r.content)

    def test_succes_et_journalisation(self):
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("Bonjour visiteur", "provider/model:free")) as m:
            r = self.post({"message": "Qui est Nick ?", "history": [{"role": "user", "text": "a"}]})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"reply": "Bonjour visiteur"})
        cfg, system_prompt, history, message = m.call_args[0]
        self.assertEqual(message, "Qui est Nick ?")
        self.assertEqual(history, [{"role": "user", "text": "a"}])
        self.assertIn("Nick", system_prompt)
        log = ChatLog.objects.get()
        self.assertEqual((log.question, log.answer, log.ok, log.model_used),
                         ("Qui est Nick ?", "Bonjour visiteur", True, "provider/model:free"))
        self.assertEqual(len(log.visitor), 16)  # empreinte, pas l'IP

    def test_journalisation_desactivee_garde_seulement_le_compteur(self):
        ChatbotSettings.objects.update(log_conversations=False)
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("secret", "m")):
            self.post({"message": "question privée"})
        log = ChatLog.objects.get()
        self.assertEqual((log.question, log.answer), ("", ""))

    def test_validations(self):
        self.assertEqual(self.post({"message": "   "}).status_code, 400)
        self.assertEqual(self.post({"message": "x" * 601}).status_code, 400)
        r = self.client.post(self.URL, "pas du json", content_type="application/json")
        self.assertEqual(r.status_code, 400)

    def test_desactive(self):
        ChatbotSettings.objects.update(enabled=False)
        self.assertEqual(self.post({"message": "hi"}).status_code, 503)

    def test_limite_par_visiteur(self):
        ChatbotSettings.objects.update(hourly_limit_per_visitor=2)
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("ok", "m")):
            codes = [self.post({"message": f"q{i}"}).status_code for i in range(4)]
        self.assertEqual(codes, [200, 200, 429, 429])

    def test_limite_par_visiteur_est_individuelle(self):
        ChatbotSettings.objects.update(hourly_limit_per_visitor=1)
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("ok", "m")):
            a = self.post({"message": "a"}, REMOTE_ADDR="1.1.1.1").status_code
            a2 = self.post({"message": "a"}, REMOTE_ADDR="1.1.1.1").status_code
            b = self.post({"message": "b"}, REMOTE_ADDR="2.2.2.2").status_code
        self.assertEqual((a, a2, b), (200, 429, 200))

    def test_limite_globale_quotidienne(self):
        ChatbotSettings.objects.update(daily_limit_global=1)
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("ok", "m")):
            a = self.post({"message": "a"}, REMOTE_ADDR="1.1.1.1").status_code
            b = self.post({"message": "b"}, REMOTE_ADDR="2.2.2.2").status_code
        self.assertEqual((a, b), (200, 429))

    def test_erreurs_openrouter_affichees_proprement(self):
        err = chatbot.AIProviderError
        with mock.patch("portfolio.views.chatbot.ask_assistant", side_effect=err("quota", "x")):
            r = self.post({"message": "a"})
        self.assertEqual(r.status_code, 429)
        self.assertIn("modèles gratuits", r.json()["error"])
        self.assertNotIn("beaucoup de demandes", r.json()["error"])
        with mock.patch("portfolio.views.chatbot.ask_assistant", side_effect=err("config", "API key not valid: AIza-SECRET")):
            r = self.post({"message": "b"})
        self.assertEqual(r.status_code, 503)
        self.assertNotIn("AIza-SECRET", r.content.decode())          # le détail technique ne fuit pas
        self.assertIn("momentanément indisponible", r.json()["error"])
        self.assertTrue(ChatLog.objects.filter(ok=False, error__startswith="config").exists())

    def test_ip_derriere_proxy(self):
        ChatbotSettings.objects.update(hourly_limit_per_visitor=1)
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("ok", "m")):
            a = self.post({"message": "a"}, HTTP_X_FORWARDED_FOR="9.9.9.9, 10.0.0.1").status_code
            b = self.post({"message": "a"}, HTTP_X_FORWARDED_FOR="9.9.9.9").status_code
        self.assertEqual((a, b), (200, 429))


@override_settings(OPENROUTER_API_KEY="test-key", GROQ_API_KEY="")
class AdminTests(TestCase):
    def setUp(self):
        seed()
        self.admin = get_user_model().objects.create_superuser("boss", "b@x.fr", "pw-test-123")
        self.client = Client()
        self.client.force_login(self.admin)

    def test_acces_protege(self):
        r = Client().get("/admin/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/admin/login/", r["Location"])

    def test_accueil_admin_est_range_comme_le_site(self):
        html = self.client.get("/admin/").content.decode()
        positions = [html.find(t) for t in (
            "Général — valable pour tout le site", "Écran 1 · Accueil", "Écran 2 · Univers 3D",
            "Écran 3 · Atelier", "Navigation (en-tête, menu) et pied de page", "Assistant IA (chatbot)")]
        self.assertTrue(all(p >= 0 for p in positions), positions)
        self.assertEqual(positions, sorted(positions))
        # l'ordre de l'atelier suit la page : 01 → 07
        atelier = [html.find(t) for t in ("Atelier 01 ·", "Atelier 02 ·", "Atelier 03 ·", "Atelier 04 ·",
                                           "Atelier 05 ·", "Atelier 06 ·", "Atelier 07 ·")]
        self.assertTrue(all(p >= 0 for p in atelier), atelier)
        self.assertEqual(atelier, sorted(atelier))
        # les entrées inutilisées ne sont plus proposées
        self.assertNotIn("étape du hero", html)
        self.assertNotIn("phrase qui défile", html)

    def test_noms_admin_correspondent_aux_titres_visibles_sur_le_site(self):
        site = {t.key: t.value for t in SiteText.objects.all()}
        html = self.client.get("/admin/").content.decode()
        for key, admin_name in (("metier_tag", "Ce qui m&#x27;anime"), ("skills_tag", "Boîte à outils"),
                                ("training_tag", "Diplôme en cours"), ("projects_tag", "Travaux récents"),
                                ("certs_tag", "Reconnaissances")):
            self.assertIn(admin_name, html, key)                    # nom admin
            self.assertIn(admin_name.replace("&#x27;", "'"), site[key])  # même nom sur le site

    def test_toutes_les_listes_et_formulaires_s_affichent(self):
        for name in ("profile", "sitetextgeneral", "sitetextaccueil", "sitetextunivers", "sitetextatelier",
                     "sitetextnavigation", "sitetextpied", "marqueeitem", "manifestostat", "focusitem",
                     "skillgroup", "trainingitem", "project", "certification", "contactitem", "navitem",
                     "chatknowledge", "chatlog"):
            r = self.client.get(reverse(f"admin:portfolio_{name}_changelist"))
            self.assertEqual(r.status_code, 200, name)
        for model, obj in ((Profile, Profile.get()), (Project, Project.objects.first()),
                           (Certification, Certification.objects.first()),
                           (ChatKnowledge, ChatKnowledge.objects.first())):
            url = reverse(f"admin:portfolio_{model._meta.model_name}_change", args=[obj.pk])
            self.assertEqual(self.client.get(url).status_code, 200, model)

    def test_chaque_section_de_texte_ne_montre_que_son_groupe(self):
        r = self.client.get(reverse("admin:portfolio_sitetextunivers_changelist"))
        html = r.content.decode()
        self.assertIn("TROU NOIR", html)
        self.assertNotIn("Bonjour, je suis", html)  # texte du groupe « accueil »
        self.assertEqual(r.context["cl"].result_count, SiteText.objects.filter(group="univers").count())

    def test_modifier_un_texte_depuis_l_admin(self):
        t = SiteText.objects.get(key="home_greet")
        url = reverse("admin:portfolio_sitetextaccueil_change", args=[t.pk])
        r = self.client.post(url, {"label": t.label, "value": "Hello, I'm", "_save": "Save"})
        self.assertEqual(r.status_code, 302, getattr(r, "context", None) and r.context["adminform"].errors)
        self.assertEqual(SiteText.objects.get(pk=t.pk).value, "Hello, I'm")
        self.assertIn("Hello, I&#x27;m", Client().get("/").content.decode())

    def test_les_textes_ne_peuvent_pas_etre_ajoutes(self):
        self.assertEqual(self.client.get(reverse("admin:portfolio_sitetextaccueil_add")).status_code, 403)

    def test_reglages_assistant_redirigent_vers_la_fiche_unique(self):
        r = self.client.get(reverse("admin:portfolio_chatbotsettings_changelist"))
        self.assertEqual(r.status_code, 302)
        form = self.client.get(r["Location"])
        self.assertEqual(form.status_code, 200)
        body = form.content.decode()
        self.assertIn("Instructions pour l", body)
        self.assertIn("Clé(s) détectée(s) : OpenRouter", body)
        self.assertIn("RÈGLES FONDAMENTALES", body)       # aperçu du prompt visible
        self.assertNotIn("test-key", body)                # mais jamais la clé

    def test_cle_absente_signalee(self):
        with override_settings(OPENROUTER_API_KEY=""):
            r = self.client.get(reverse("admin:portfolio_chatbotsettings_change", args=[ChatbotSettings.get().pk]))
        self.assertIn("Aucune clé", r.content.decode())

    def test_instructions_modifiables_et_prises_en_compte(self):
        cfg = ChatbotSettings.get()
        data = {f: getattr(cfg, f) for f in (
            "assistant_name", "welcome_message", "placeholder", "suggestions", "model_name", "temperature",
            "max_output_tokens", "max_message_chars", "history_messages", "hourly_limit_per_visitor",
            "daily_limit_global", "unavailable_message")}
        data.update(enabled="on", log_conversations="on", instructions="Parle comme un pirate.", _save="Save")
        r = self.client.post(reverse("admin:portfolio_chatbotsettings_change", args=[cfg.pk]), data)
        self.assertEqual(r.status_code, 302, getattr(r, "context", None) and r.context["adminform"].errors)
        self.assertIn("Parle comme un pirate.", chatbot.build_system_prompt())

    def test_ajout_d_une_connaissance_via_l_admin(self):
        r = self.client.post(reverse("admin:portfolio_chatknowledge_add"), {
            "title": "Hobby", "kind": "info", "content": "Nick joue aux échecs.", "active": "on",
            "order": 50, "_save": "Save"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("Nick joue aux échecs.", chatbot.build_system_prompt())

    def test_diagnostic_fournisseurs(self):
        url = reverse("admin:portfolio_chat_diagnostic")
        with mock.patch.object(chatbot, "available_free_models", return_value=["provider/model:free"]), \
             mock.patch.object(chatbot, "ask_assistant", return_value=("Bonjour !", "provider/model:free")):
            ok = self.client.get(url).content.decode()
        self.assertIn("✔ OK", ok)
        self.assertIn("Bonjour !", ok)
        with mock.patch.object(
                chatbot, "available_free_models",
                side_effect=chatbot.AIProviderError("config", "Invalid API key")):
            ko = self.client.get(url).content.decode()
        self.assertIn("✘ Échec", ko)
        self.assertEqual(Client().get(url).status_code, 302)    # réservé aux administrateurs

    def test_journal_des_conversations_en_lecture_seule(self):
        log = ChatLog.objects.create(visitor="abc", question="Salut ?", answer="Oui")
        r = self.client.get(reverse("admin:portfolio_chatlog_change", args=[log.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:portfolio_chatlog_add")).status_code, 403)
        self.assertIn("Salut ?", self.client.get(reverse("admin:portfolio_chatlog_changelist")).content.decode())


# ════════════════════════════════════════════════════════════════════════
#  Univers 3D : textes éditables + aide de l'assistant
# ════════════════════════════════════════════════════════════════════════
class UniverseTests(TestCase):
    def setUp(self):
        seed()

    def test_les_astres_sont_seedes_avec_les_textes_d_origine(self):
        keys = set(UniverseBody.objects.values_list("key", flat=True))
        self.assertEqual(keys, {"sun", "saturnia", "verdania", "jovis9", "ignis", "cryos",
                                "blackhole", "station", "galaxy", "kuiper", "crystals"})
        self.assertEqual(UniverseBody.objects.get(key="saturnia").subtitle, "FORMATION ESATIC")
        self.assertEqual(UniverseBody.objects.get(key="blackhole").info, "")

    def test_les_cles_utilisees_par_le_js_existent_dans_l_admin(self):
        js = (PORTFOLIO / "static" / "portfolio" / "js" / "hyperspace.js").read_text(encoding="utf-8")
        used = set(re.findall(r"\btx\('([a-z0-9]+)'", js)) | set(re.findall(r"^\s+key: '([a-z0-9]+)',", js, re.M))
        self.assertTrue(len(used) >= 11, used)
        self.assertEqual(sorted(used - set(UniverseBody.objects.values_list("key", flat=True))), [])

    def test_modifier_un_astre_change_les_donnees_envoyees_a_la_3d(self):
        UniverseBody.objects.filter(key="ignis").update(name="NOUVEAU NOM", info="Nouvelle transmission")
        html = Client().get("/").content.decode()
        raw = re.search(r'<script id="hs-data" type="application/json">(.*?)</script>', html, re.S).group(1)
        bodies = {b["key"]: b for b in json.loads(raw)["bodies"]}
        self.assertEqual(bodies["ignis"]["name"], "NOUVEAU NOM")
        self.assertEqual(bodies["ignis"]["info"], "Nouvelle transmission")
        self.assertEqual(len(bodies), 11)

    def test_le_seed_ne_reecrit_pas_les_astres(self):
        UniverseBody.objects.filter(key="cryos").update(info="Mon texte à moi")
        seed()
        self.assertEqual(UniverseBody.objects.get(key="cryos").info, "Mon texte à moi")
        seed("--reset")
        self.assertIn("stage de fin de cycle", UniverseBody.objects.get(key="cryos").info)

    def test_le_guide_contient_tout_ce_qu_il_faut_pour_se_reperer(self):
        guide = chatbot.universe_guide()
        for needle in ("SINGULARITÉ", "TROISIÈME PARTIE", "Atelier", "flèche", "radar", "RADAR STELLAIRE",
                       "SATURNIA", "VERDANIA", "JOVIS-9", "IGNIS", "CRYOS", "SOLEIL ALPHA",
                       "TRANSMISSION STELLAIRE", "ARCHE ORBITALE", "GALAXIE SPIRALE",
                       "Entrer dans mon univers", "Propulsion", "ZQSD", "JOYSTICK"):
            self.assertIn(needle, guide, needle)
        self.assertIn(Project.objects.first().title, guide)       # chaque projet = un astre
        self.assertNotIn("[", guide)                              # crochets de mise en forme retirés

    def test_le_guide_suit_les_modifications_de_l_admin(self):
        UniverseBody.objects.filter(key="blackhole").update(name="PORTAIL ZÉRO")
        SiteText.objects.filter(key="hs_cmds_pc_body").update(value="[W] avancer · [X] freiner")
        guide = chatbot.universe_guide()
        self.assertIn("PORTAIL ZÉRO", guide)
        self.assertIn("W avancer · X freiner", guide)

    def test_le_prompt_contient_la_regle_et_le_guide_de_l_univers(self):
        prompt = chatbot.build_system_prompt()
        self.assertIn("GUIDE DE L'UNIVERS 3D", prompt)
        self.assertIn("cet univers", prompt)                      # règle d'interprétation
        self.assertNotIn("CONTEXTE ACTUEL", prompt)               # pas de contexte sans écran

    def test_le_contexte_d_ecran_est_ajoute_au_prompt(self):
        self.assertIn("UNIVERS 3D, en plein vol", chatbot.build_system_prompt(screen="universe"))
        self.assertIn("perdu", chatbot.build_system_prompt(screen="universe"))
        self.assertIn("l'Atelier", chatbot.build_system_prompt(screen="atelier"))
        self.assertNotIn("CONTEXTE ACTUEL", chatbot.build_system_prompt(screen="n'importe quoi"))

    @override_settings(OPENROUTER_API_KEY="test-key", GROQ_API_KEY="")
    def test_l_api_transmet_l_ecran_au_prompt(self):
        c = Client()
        with mock.patch("portfolio.views.chatbot.ask_assistant", return_value=("ok", "m")) as m:
            c.post("/api/chat/", json.dumps({"message": "Dis-moi tout sur cet univers", "screen": "universe"}),
                   content_type="application/json")
            c.post("/api/chat/", json.dumps({"message": "x", "screen": "<script>"}),
                   content_type="application/json")
        self.assertIn("UNIVERS 3D, en plein vol", m.call_args_list[0][0][1])
        self.assertNotIn("CONTEXTE ACTUEL", m.call_args_list[1][0][1])


class ChatWidgetConfigTests(TestCase):
    def setUp(self):
        seed()

    def config(self):
        html = Client().get("/").content.decode()
        raw = re.search(r'<script id="chatbot-config" type="application/json">(.*?)</script>', html, re.S).group(1)
        return json.loads(raw)

    def test_suggestions_par_defaut_incluent_l_univers(self):
        cfg = self.config()
        self.assertEqual(cfg["suggestions"][0], "Dis-moi tout sur cet univers")
        self.assertEqual(cfg["universeSuggestions"][0], "Dis-moi tout sur cet univers")
        self.assertIn("Comment me déplacer ?", cfg["universeSuggestions"])
        self.assertIn("Où est le trou noir ?", cfg["universeSuggestions"])
        self.assertEqual(cfg["alertText"], "Perdu ? Demandez-moi !")
        self.assertTrue(cfg["subtitle"])

    def test_reglages_modifiables_remontent_dans_le_widget(self):
        ChatbotSettings.objects.update(universe_suggestions="A ?\nB ?", universe_alert_text="Aide !",
                                       header_subtitle="Sous-titre perso")
        cfg = self.config()
        self.assertEqual((cfg["universeSuggestions"], cfg["alertText"], cfg["subtitle"]),
                         (["A ?", "B ?"], "Aide !", "Sous-titre perso"))
        self.assertIn("Sous-titre perso", Client().get("/").content.decode())

    def test_ancien_defaut_des_suggestions_est_mis_a_jour_mais_pas_une_liste_personnalisee(self):
        old = ("Qui est Nick ?\nQuels sont ses projets les plus marquants ?\n"
               "Quelles certifications a-t-il obtenues ?\nEst-il disponible pour un stage ?")
        ChatbotSettings.objects.update(suggestions=old)
        call_command("seed_chatbot", stdout=StringIO())
        self.assertIn("Dis-moi tout sur cet univers", ChatbotSettings.get().suggestions)
        ChatbotSettings.objects.update(suggestions="Ma question perso ?")
        call_command("seed_chatbot", stdout=StringIO())
        self.assertEqual(ChatbotSettings.get().suggestions, "Ma question perso ?")

    def test_le_widget_n_utilise_pas_de_balises_header_ni_section(self):
        """Régression : style.css applique `header{position:fixed;...}` et `section{...}`
        à ces balises, ce qui faisait chevaucher l'en-tête du chat sur les messages."""
        tpl = (PORTFOLIO / "templates" / "portfolio" / "_chatbot.html").read_text(encoding="utf-8")
        tpl = re.sub(r"\{% comment %\}.*?\{% endcomment %\}", "", tpl, flags=re.S)   # jamais rendu
        for tag in ("<header", "<section", "<footer", "<main", "<nav", "<aside", "<article"):
            self.assertNotIn(tag, tpl, tag)

    def test_les_selecteurs_globaux_de_style_css_ne_touchent_pas_le_widget(self):
        css = (PORTFOLIO / "static" / "portfolio" / "css" / "style.css").read_text(encoding="utf-8")
        tpl = (PORTFOLIO / "templates" / "portfolio" / "_chatbot.html").read_text(encoding="utf-8")
        tpl = re.sub(r"\{% comment %\}.*?\{% endcomment %\}", "", tpl, flags=re.S)
        used_tags = set(re.findall(r"<([a-z][a-z0-9]*)", tpl))
        globals_ = set(re.findall(r"^([a-z][a-z0-9]*)\s*[{,]", css, re.M))
        risky = {"header", "section", "footer", "main", "nav", "aside", "article", "form", "label", "textarea"}
        self.assertEqual(sorted(used_tags & globals_ & risky), [])

    def test_assets_du_chat_et_du_rafraichissement_sont_charges(self):
        html = Client().get("/").content.decode()
        for asset in ("chatbot.css", "chatbot.js", "refresh.css", "refresh.js"):
            self.assertIn(asset, html, asset)

    def test_le_bouton_peut_etre_deplace_dans_l_univers_sur_mobile(self):
        css = (PORTFOLIO / "static" / "portfolio" / "css" / "chatbot.css").read_text(encoding="utf-8")
        js = (PORTFOLIO / "static" / "portfolio" / "js" / "chatbot.js").read_text(encoding="utf-8")
        tpl = (PORTFOLIO / "templates" / "portfolio" / "_chatbot.html").read_text(encoding="utf-8")
        self.assertIn(".cb.is-movable .cb-toggle{touch-action:none", css)
        self.assertIn("toggle.addEventListener('pointerdown'", js)
        self.assertIn("toggle.addEventListener('pointermove'", js)
        self.assertIn("screen === 'universe' && !isOpen()", js)
        self.assertIn("faire glisser pour déplacer le bouton dans l'univers", tpl)


@override_settings(OPENROUTER_API_KEY="test-key", GROQ_API_KEY="")
class UniverseAdminTests(TestCase):
    def setUp(self):
        seed()
        self.client = Client()
        self.client.force_login(get_user_model().objects.create_superuser("boss", "b@x.fr", "pw-test-123"))

    def test_les_astres_sont_dans_le_bloc_univers_3d(self):
        html = self.client.get("/admin/").content.decode()
        start = html.find("Écran 2 · Univers 3D")
        end = html.find("Écran 3 · Atelier")
        self.assertTrue(0 <= start < end)
        self.assertIn("Univers 3D · astres", html[start:end])
        self.assertIn("textes, commandes et messages", html[start:end])

    def test_liste_et_modification_d_un_astre(self):
        r = self.client.get(reverse("admin:portfolio_universebody_changelist"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("SATURNIA", r.content.decode())
        b = UniverseBody.objects.get(key="verdania")
        r = self.client.post(reverse("admin:portfolio_universebody_change", args=[b.pk]),
                             {"name": "VERDANIA", "subtitle": "CE QUI M'ANIME", "info": "Texte modifié", "_save": "Save"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(UniverseBody.objects.get(pk=b.pk).info, "Texte modifié")

    def test_pas_d_ajout_ni_de_suppression_d_astres(self):
        self.assertEqual(self.client.get(reverse("admin:portfolio_universebody_add")).status_code, 403)
        b = UniverseBody.objects.first()
        self.assertEqual(self.client.get(reverse("admin:portfolio_universebody_delete", args=[b.pk])).status_code, 403)

    def test_reglages_du_chat_proposent_les_champs_de_l_univers(self):
        r = self.client.get(reverse("admin:portfolio_chatbotsettings_change", args=[ChatbotSettings.get().pk]))
        body = r.content.decode()
        for field in ("universe_suggestions", "universe_alert_text", "header_subtitle"):
            self.assertIn(f'name="{field}"', body, field)


# ════════════════════════════════════════════════════════════════════════
#  Intégrité du rendu : ces tests auraient détecté le bug « chat invisible dans l'univers »
# ════════════════════════════════════════════════════════════════════════
from html.parser import HTMLParser

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Ancestors(HTMLParser):
    """Relève la chaîne de balises ouvertes autour d'un élément (par son id)."""

    def __init__(self, target_id):
        super().__init__()
        self.target, self.stack, self.found = target_id, [], None

    def handle_starttag(self, tag, attrs):
        if dict(attrs).get("id") == self.target:
            self.found = list(self.stack)
        if tag not in _VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            while self.stack and self.stack.pop() != tag:
                pass


class RenderIntegrityTests(TestCase):
    def setUp(self):
        seed()
        self.html = Client().get("/").content.decode()

    def test_aucune_syntaxe_de_gabarit_ne_fuit_dans_la_page(self):
        for token in ("{#", "#}", "{%", "%}", "style.css leur applique"):
            self.assertNotIn(token, self.html, token)

    def test_les_commentaires_de_gabarit_tiennent_sur_une_seule_ligne(self):
        """Django n'interprète `{# … #}` que sur UNE ligne ; sinon le texte s'affiche tel quel
        (et ses éventuelles balises HTML sont interprétées par le navigateur)."""
        for f in (PORTFOLIO / "templates").rglob("*.html"):
            text = f.read_text(encoding="utf-8")
            for m in re.finditer(r"\{#", text):
                rest = text[m.end():]
                end_line = rest.find("\n") if "\n" in rest else len(rest)
                self.assertTrue(0 <= rest.find("#}") < end_line, f"{f.name} : commentaire {{# sur plusieurs lignes")

    def test_le_widget_est_enfant_direct_du_body(self):
        """Imbriqué dans un <header> (z-index 200), le chat disparaissait sous l'univers 3D (#ui-b, z-index 500)."""
        parser = _Ancestors("chatbot")
        parser.feed(self.html)
        self.assertEqual(parser.found, ["html", "body"], parser.found)

    def test_le_widget_n_a_aucun_ancetre_qui_cree_un_contexte_d_empilement(self):
        for element_id in ("cb-toggle", "cb-panel", "cb-backdrop"):
            parser = _Ancestors(element_id)
            parser.feed(self.html)
            self.assertEqual(parser.found, ["html", "body", "div"], element_id)

    def test_les_elements_fixes_du_chat_passent_au_dessus_de_l_univers_3d(self):
        css = (PORTFOLIO / "static" / "portfolio" / "css" / "style.css").read_text(encoding="utf-8")
        chat = (PORTFOLIO / "static" / "portfolio" / "css" / "chatbot.css").read_text(encoding="utf-8")
        ui_b_z = int(re.search(r"\.app-ui-b #ui-b \{[^}]*?z-index:\s*(\d+)", css).group(1))
        toggle_z = int(re.search(r"\.cb-toggle\{[^}]*?z-index:(\d+)", chat).group(1))
        panel_z = int(re.search(r"\.cb-panel\{[^}]*?z-index:(\d+)", chat).group(1))
        self.assertGreater(toggle_z, ui_b_z)
        self.assertGreater(panel_z, ui_b_z)

    def test_aucune_regle_ne_cache_le_chat_dans_l_univers(self):
        chat = (PORTFOLIO / "static" / "portfolio" / "css" / "chatbot.css").read_text(encoding="utf-8")
        self.assertNotRegex(chat, r"app-ui-b[^{]*\.cb[^{]*\{[^}]*display:\s*none")

    def test_la_page_se_ferme_correctement(self):
        parser = _Ancestors("__none__")
        parser.feed(self.html)
        self.assertEqual(parser.stack, [], "balises restées ouvertes : %s" % parser.stack)


@override_settings(OPENROUTER_API_KEY="test-key", GROQ_API_KEY="")
class RobustnessTests(TestCase):
    def setUp(self):
        seed()
        chatbot._models_cache.update(models=[], at=0.0)
        chatbot._groq_models_cache.update(models=[], at=0.0)
        self.cfg = ChatbotSettings.get()
        self.models = {"data": [
            {"id": "provider/model-a:free"},
            {"id": "provider/model-b:free"},
        ]}

    def test_surcharge_503_bascule_vers_un_modele_de_secours(self):
        attempted = []

        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, self.models
            attempted.append(body["model"])
            if len(attempted) == 1:
                return 503, {"error": {"message": "Provider overloaded"}}
            return 200, {"choices": [{"message": {"content": "Réponse de secours"}}]}

        with mock.patch.object(chatbot, "_http", fake):
            reply, model = chatbot.ask_assistant(self.cfg, "S", [], "q")
        self.assertEqual((reply, model), ("Réponse de secours", "openrouter:provider/model-b:free"))
        self.assertEqual(attempted, ["provider/model-a:free", "provider/model-b:free"])

    def test_tous_les_modeles_en_quota_remontent_une_erreur_quota(self):
        def fake(method, url, key, body=None):
            if method == "GET":
                return 200, self.models
            return 429, {"error": {"message": "rate limit"}}

        with mock.patch.object(chatbot, "_http", fake):
            with self.assertRaises(chatbot.AIProviderError) as cm:
                chatbot.ask_assistant(self.cfg, "S", [], "q")
        self.assertEqual(cm.exception.kind, "quota")
        self.assertEqual(cm.exception.status, 429)

    def test_detail_technique_visible_uniquement_des_administrateurs_connectes(self):
        err = chatbot.AIProviderError("config", "API key not valid. Please pass a valid API key.", 400)

        def post(client):
            with mock.patch("portfolio.views.chatbot.ask_assistant", side_effect=err):
                return client.post("/api/chat/", json.dumps({"message": "salut"}), content_type="application/json")

        visiteur = post(Client())
        self.assertEqual(visiteur.status_code, 503)
        self.assertNotIn("debug", visiteur.json())
        self.assertNotIn("API key not valid", visiteur.content.decode())

        staff = Client()
        staff.force_login(get_user_model().objects.create_superuser("boss", "b@x.fr", "pw-test-123"))
        resp = post(staff)
        self.assertIn("config", resp.json()["debug"])
        self.assertIn("API key not valid", resp.json()["debug"])
        self.assertIn("momentanément indisponible", resp.json()["error"])   # le visiteur voit toujours ce message
