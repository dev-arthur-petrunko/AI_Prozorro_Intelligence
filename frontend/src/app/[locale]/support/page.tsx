"use client";

import { useTranslations } from "next-intl";
import { Heart, Target, Cpu, Copy, ExternalLink } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const JAR_URL = "https://send.monobank.ua/jar/AZ9XsVXgGU";
const CARD_NUMBER = "4874 1000 3119 6366";

const BUDGET: { component: string; purpose: string; cost: string }[] = [
  { component: "Відеокарта: RTX 3090 24GB (Б/В)", purpose: 'Головний "мозок" — 24 ГБ VRAM для локальних моделей (Llama, Qwen)', cost: "48 000–52 000" },
  { component: "Процесор: Intel Core i5-12400F", purpose: "Базова обчислювальна підтримка", cost: "7 000" },
  { component: "Материнська плата: LGA1700 (B660/B760)", purpose: "Стабільна платформа для цілодобової роботи", cost: "5 000" },
  { component: "Оперативна пам'ять: 64 GB DDR4", purpose: "Обробка великих масивів текстів, буферизація", cost: "7 500" },
  { component: "SSD NVMe M.2 2 TB", purpose: "Зберігання бази ProZorro, векторний пошук (Qdrant)", cost: "6 000" },
  { component: "Блок живлення 750–850W (80+ Gold)", purpose: "Стабільне живлення під навантаженням GPU", cost: "4 500" },
  { component: "Корпус та охолодження", purpose: "Відведення тепла для безперервної роботи", cost: "4 000" },
  { component: "ІБП (UPS)", purpose: "Захист від відключень світла", cost: "6 500" },
  { component: "Домен .com.ua (1 рік)", purpose: "Офіційна адреса проєкту", cost: "600" },
];

export default function SupportPage() {
  const t = useTranslations("nav");

  const copyCard = () => {
    navigator.clipboard?.writeText(CARD_NUMBER.replace(/\s/g, ""));
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="flex items-center gap-2 text-2xl font-bold">
        <Heart className="h-6 w-6 text-red-500" />
        {t("support")}
      </h1>

      {/* Місія автора */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Target className="h-4 w-4 text-primary" />
            Про проєкт та мету
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>
            Мене звати <span className="font-medium text-foreground">Петрунько Артур</span>. Ціль цього
            проєкту — не заробити, а створити чесний AI-аналіз закупівель для країни, яка на це заслуговує.
            Я переконаний: саме за допомогою штучного інтелекту можна забезпечити чесні тендери та системно
            зменшити корупцію.
          </p>
          <p>
            Зараз на етапі держзакупівель немає інтелектуального зіставлення товарів з їхніми реальними
            ринковими цінами. Якщо така система запрацює, вона чітко покаже прозорість закупівель і те, куди
            йдуть зайві кошти. За попередніми оцінками, йдеться про мільярди гривень, які можна зберегти для
            країни щороку.
          </p>
        </CardContent>
      </Card>

      {/* Поточний стан */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Cpu className="h-4 w-4 text-primary" />
            Поточний стан проєкту
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>
            Зараз на{" "}
            <a
              href="https://ai-prozorro-intelligence.vercel.app/uk/dashboard"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              ai-prozorro-intelligence.vercel.app/uk/dashboard
              <ExternalLink className="h-3 w-3" />
            </a>{" "}
            вже працюють 2 аналізи. Але через обмежені обчислювальні ресурси зараз застосовується слабка
            AI-модель, і аналіз побудований так: спочатку розраховується Індекс ризику (AI) на основі
            математичних методів, і лише потім AI підключається до аналізу — тільки для найкритичніших
            випадків. Через нехватку ресурсів система поки що не має оцінки відповідності цін ринковим —
            а саме це найважливіша функція для виявлення переплат.
          </p>
        </CardContent>
      </Card>

      {/* Приклад переплати */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Чому це критично</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm leading-relaxed text-muted-foreground">
          <p>
            Наприклад, нещодавно на ProZorro держустанова закупила 50 клавіатур по 450 грн за штуку. Та сама
            модель на Rozetka коштує ~250 грн у роздріб (без оптової знижки). Різниця:
          </p>
          <ul className="space-y-1 rounded-md border border-border bg-muted/30 p-4">
            <li>Заплачено: <span className="font-medium text-foreground">50 × 450 грн = 22 500 грн</span></li>
            <li>Ринкова ціна: <span className="font-medium text-foreground">50 × 250 грн = 12 500 грн</span></li>
            <li className="text-foreground">
              Переплата: <span className="font-semibold text-red-500">10 000 грн</span> лише на одній
              закупівлі клавіатур — і це без урахування опту, який знизив би ціну ще більше
            </li>
          </ul>
          <p>
            Якщо помножити такі випадки на тисячі тендерів щорічно — йдеться про мільярди гривень переплат.
            Саме для виявлення таких кейсів автоматично, в масштабі всієї системи ProZorro, і потрібна
            повноцінна локальна LLM зі зіставленням цін з реальним ринком — а не лише математичний індекс ризику.
          </p>
          <p>
            У майбутньому я готовий розвинути проєкт до масштабнішого варіанту, передати його або повністю
            адаптувати для держслужби та вищестоящих органів для покращення їхньої роботи. Зараз і надалі
            проєкт буде <span className="font-medium text-foreground">повністю безкоштовним для всіх</span>.
            У перспективі контролюючі органи та суспільство зможуть отримувати додаткову аналітику про
            закупівлі, перевіряти їх на відповідність ринковим цінам і системно протидіяти корупції.
          </p>
          <p>
            Саме тому відкрито збір коштів — це мінімум, необхідний для запуску локального проєкту, щоб не
            залежати від сторонніх AI-сервісів і щомісячних підписок. Для аналізу чутливих державних даних
            потрібна власна локальна LLM, налаштована під конкретну специфіку роботи з тендерами.
          </p>
        </CardContent>
      </Card>

      {/* Кошторис */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Кошторис мінімального локального сервера</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm leading-relaxed text-muted-foreground">
            Розрахунок обладнання «під ключ» для розгортання автономної станції та локального аналізу
            даних ProZorro:
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="px-3 py-2 font-medium text-muted-foreground">Компонент</th>
                  <th className="px-3 py-2 font-medium text-muted-foreground">Призначення в проєкті</th>
                  <th className="px-3 py-2 text-right font-medium text-muted-foreground">Вартість (грн)</th>
                </tr>
              </thead>
              <tbody>
                {BUDGET.map((row, i) => (
                  <tr key={i} className="border-b border-border/50">
                    <td className="px-3 py-2 font-medium text-foreground">{row.component}</td>
                    <td className="px-3 py-2 text-muted-foreground">{row.purpose}</td>
                    <td className="px-3 py-2 text-right font-mono text-foreground">{row.cost}</td>
                  </tr>
                ))}
                <tr className="bg-muted/30">
                  <td className="px-3 py-2 font-semibold text-foreground">РАЗОМ</td>
                  <td className="px-3 py-2 text-muted-foreground">Незалежна апаратна база для старту</td>
                  <td className="px-3 py-2 text-right font-mono font-semibold text-foreground">~101 600–105 600</td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Реквізити */}
      <Card className="border-primary/40">
        <CardHeader>
          <CardTitle className="text-base">🎯 Ціль: 105 600,00 ₴</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <a
            href={JAR_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 font-medium text-primary-foreground hover:opacity-90"
          >
            <Heart className="h-4 w-4" />
            Підтримати на банку monobank
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
          <div className="space-y-1">
            <p className="text-muted-foreground">🔗 Посилання на банку:</p>
            <a
              href={JAR_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="break-all text-primary hover:underline"
            >
              {JAR_URL}
            </a>
          </div>
          <div className="space-y-1">
            <p className="text-muted-foreground">💳 Номер картки банки:</p>
            <div className="flex items-center gap-2">
              <code className="rounded bg-muted px-2 py-1 font-mono text-foreground">{CARD_NUMBER}</code>
              <button
                onClick={copyCard}
                className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-accent"
              >
                <Copy className="h-3 w-3" />
                Копіювати
              </button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
