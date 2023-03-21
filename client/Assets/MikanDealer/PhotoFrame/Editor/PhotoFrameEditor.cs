
using UnityEngine;
using VRC.SDKBase;

using UnityEditor;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEditor.PackageManager;
using System.Security.Policy;

namespace MikanDealer
{
	[CustomEditor(typeof(PhotoFrameManager))]
	public class MonoBehaviourModelEditor : Editor
	{
		PhotoFrameManager _Instance = null;

		private string BASE_URL = "https://photoframe-a3miq2wxma-an.a.run.app/";
		private Dictionary<string, object> PhotoTable = null;

		void Awake()
		{
			EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
		}

		private void OnPlayModeStateChanged(PlayModeStateChange state)
		{
			if (state == PlayModeStateChange.ExitingEditMode)
			{
				foreach (var frame in SelectPhotoFrames())
				{
					ClearTexture(frame);
				}
			}
		}

		void OnEnable()
		{
			_Instance = target as PhotoFrameManager;
			LoadEnv();
		}

		public override void OnInspectorGUI()
		{
			//base.OnInspectorGUI();

			GUIStyle style = new GUIStyle(GUI.skin.label);
			style.wordWrap = true;
			GUIStyle bold = new GUIStyle(GUI.skin.label);
			bold.wordWrap = true;
			bold.fontStyle = FontStyle.Bold;

			EditorGUILayout.LabelField("1. Spread Sheet URL には、次のようなスプレッドシートの URL を入力 (例) https://docs.google.com/spreadsheets/d/hoge/\n1列目をid、2列目を画像URL、3列目以降は自由です。", style);
			EditorGUILayout.LabelField("※ スプレッドシートの共有「リンクを知っている全員」「閲覧者」に必ずして下さい ※", bold);
			_Instance.SpreadSheetUrl = EditorGUILayout.TextField("Spread Sheet Url", _Instance.SpreadSheetUrl);
			EditorGUILayout.LabelField("");

			EditorGUILayout.LabelField("2. Work Sheet には、スプレッドシート下部のワークシート(タブ)の名前を入力", style);
			_Instance.WorkSheet = EditorGUILayout.TextField("Work Sheet", _Instance.WorkSheet);
			EditorGUILayout.LabelField("");

			EditorGUILayout.LabelField("3. 子オブジェクトの Photo Frame のインスペクター内の id を表示したい画像のものを入力", style);
			EditorGUILayout.LabelField("Photo Frame Manager は、この子オブジェクトだけの画像を管理します", style);
			EditorGUILayout.LabelField("");

			EditorGUILayout.LabelField("4. 「仮表示」で、スプレッドシートからURLの画像を読み込み仮表示", style);
			if (GUILayout.Button("仮表示"))
			{
				EditorCoroutine.Start(UpdatingPhotoFrames(_Instance.SpreadSheetUrl, _Instance.WorkSheet));
			}
			EditorGUILayout.LabelField("");

			EditorGUILayout.LabelField("5. オプション", style);
			EditorGUILayout.LabelField("●アップロードするワールドに画像を含めたい場合は、このままワールドのビルドを行ってください。Webからの画像の読み込みが終わり次第、最新の画像に変わります。", style);
			EditorGUILayout.LabelField("●アップロードするワールドに画像を含めたくない場合は、以下の「クリア」を押してください。ワールド容量を軽くできますが、Webからの画像読み込みが終わるまでは表示されません。", style);
			if (GUILayout.Button("クリア"))
			{
				EditorCoroutine.Start(ClearingPhotoFrames(_Instance.SpreadSheetUrl, _Instance.WorkSheet));
			}
		}

		private string GetSpreadSheetKey(string url)
		{
			Match match = Regex.Match(url, "https://docs.google.com/spreadsheets/d/([a-zA-Z0-9_-]+)/");
			if (match.Success) return match.Groups[1].Value;

			Debug.LogError("スプレッドシートのURLを入力してください (例) https://docs.google.com/spreadsheets/d/hoge/");
			return null;
		}

		private bool Validate(string key, string worksheet)
		{
			if (string.IsNullOrEmpty(worksheet))
			{
				Debug.LogError("ワークシートが入力されていません");
				return false;
			}
			return true;
		}

		private IEnumerator UpdatingPhotoFrames(string url, string worksheet)
		{
			string key = GetSpreadSheetKey(url);
			if (string.IsNullOrEmpty(key) || !Validate(key, worksheet)) yield break;

			foreach (var frame in SelectPhotoFrames()) frame.AssignLoading();

			string api = BASE_URL + "sheet/" + key + "/" + worksheet + ".json";
			using (UnityWebRequest www = UnityWebRequest.Get(api))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.isHttpError || www.isNetworkError)
				{
					Debug.LogError("Sheet API: " + api + "\n" + www.error);
					yield break;
				}
				string[] lines = www.downloadHandler.text.Split('\n');
				if (lines[0] != "OK")
				{
					Debug.LogError("スプレッドシートからデータの読み込みに失敗しました\n" + lines[1]);
					yield break;
				}
				PhotoTable = new Dictionary<string, object>();
				foreach (var o in Json.Deserialize(lines[1]) as List<object>)
				{
					var box = o as Dictionary<string, object>;
					if (box.ContainsKey("id") && !string.IsNullOrEmpty((string)box["id"])) PhotoTable[(string)box["id"]] = box;
				}
			}

			foreach(var frame in SelectPhotoFrames())
			{
				EditorCoroutine.Start(AssigningWebTexture(frame));
				yield return new WaitForSecondsRealtime(1f);
			}
		}

		private IEnumerator ClearingPhotoFrames(string url, string worksheet)
		{
			foreach (var frame in SelectPhotoFrames())
			{
				ClearTexture(frame);
			}

			string key = GetSpreadSheetKey(url);
			if (string.IsNullOrEmpty(key) || !Validate(key, worksheet)) yield break;

			string api = BASE_URL + "clear/" + key + "/" + worksheet;
			Debug.Log(api);
			using (UnityWebRequest www = UnityWebRequest.Get(api))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.isHttpError || www.isNetworkError)
				{
					Debug.LogError(www.error);
					yield break;
				}

				string[] lines = www.downloadHandler.text.Split('\n');
				if (lines[0] != "OK" && lines.Length > 1)
				{
					Debug.LogError(lines[1]);
					yield break;
				}
			}
		}

		private PhotoFrame[] SelectPhotoFrames()
		{
			if (_Instance == null) return new PhotoFrame[] { };

			var frames = _Instance.transform.GetComponentsInChildren<PhotoFrame>();
			foreach (var frame in frames)
			{
				if (string.IsNullOrEmpty(frame.ID)) frame.ID = frame.gameObject.name;
			}
			return frames;
		}

		private IEnumerator AssigningWebTexture(PhotoFrame frame)
		{
			if (PhotoTable.ContainsKey(frame.ID))
			{
				var box = PhotoTable[frame.ID] as Dictionary<string, object>;
				frame.Url = new VRCUrl(box["url"] as string);
			}
			else
			{
				frame.Url = null;
				yield break;
			}

			string url = frame.Url.Get();
			if (url == null) yield break;

			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) yield break;

			using (UnityWebRequest www = UnityWebRequestTexture.GetTexture(url))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.isHttpError || www.isNetworkError)
				{
					Debug.LogError("Image URL: " + url + "\n" + www.error);
				}
				else
				{
					Material copied = new Material(renderer.sharedMaterial);
					Texture2D tex = ((DownloadHandlerTexture)www.downloadHandler).texture;
					copied.mainTexture = tex;
					renderer.sharedMaterial = copied;
					if (frame.AutoAdjust) frame.AdjustTexture(tex);
				}
			}
		}

		private void ClearTexture(PhotoFrame frame)
		{
			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) return;

			renderer.sharedMaterial.mainTexture = null;
		}

		private void LoadEnv()
		{
			string path = System.IO.Path.Combine(Application.dataPath, "MikanDealer/PhotoFrame/env.json");
			if (System.IO.File.Exists(path))
			{
				var data = Json.Deserialize(System.IO.File.ReadAllText(path)) as Dictionary<string, object>;
				if (!string.IsNullOrEmpty(data["BASE_URL"] as string))
				{
					BASE_URL = data["BASE_URL"] as string;
					Debug.Log("BASE_URL is overwritten :" + BASE_URL);
				}
			}
		}
	}
}