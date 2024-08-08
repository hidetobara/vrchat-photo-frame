
using UnityEngine;
using VRC.SDKBase;

using System;
using UnityEditor;
using UnityEngine.Networking;
using System.Collections;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEditor.PackageManager;
using System.Security.Policy;
using System.Security.Permissions;

namespace MikanDealer
{
	public class FrameSheet
	{
		public string EndPointUrl;
		public string SheetKey;
		public string Worksheet;
	}

	public class PhotoItem
	{
		public enum TYPE { UNKNOWN, G_DRIVE, G_PHOTOS }

		public string PublicUrl;
		public string SrcUrl;
		public string ID;
		public string Title;
		public TYPE Type = TYPE.UNKNOWN;

		private PhotoItem() { }

		public static PhotoItem Parse(FrameSheet sheet, string id)
		{
			PhotoItem i = new PhotoItem() { ID = id };
			return i;
		}

		public static PhotoItem Parse(FrameSheet sheet, Dictionary<string, object> o)
		{
			if (o == null) return null;

			PhotoItem i = new PhotoItem();
			try
			{
				if (o.ContainsKey("public")) i.PublicUrl = (string)o["public"];
				if (o.ContainsKey("url")) i.SrcUrl = (string)o["url"];
				if (o.ContainsKey("id")) i.ID = (string)o["id"];
				if (o.ContainsKey("title")) i.Title = (string)o["title"];
				if (o.ContainsKey("type"))
				{
					if ((string)o["type"] == TYPE.G_PHOTOS.ToString()) i.Type = TYPE.G_PHOTOS;
					if ((string)o["type"] == TYPE.G_DRIVE.ToString()) i.Type = TYPE.G_DRIVE;
				}
				return i;
			}
			catch(Exception ex)
			{
				Debug.LogException(ex);
				return null;
			}
		}
	}

	[CustomEditor(typeof(SyncFrameManager))]
	public class MonoBehaviourModelEditor : Editor
	{
		SyncFrameManager _Instance = null;

//		private string BASE_URL = "https://photo-frame-cache-ow7nx6wgvq-an.a.run.app/";
		private string BASE_URL = "http://localhost:8080/";
		private FrameSheet CurrentSheet = null;
		private Dictionary<string, PhotoItem> PhotoTable = null;
		private IEnumerator Lock;

		void Awake()
		{
			EditorApplication.playModeStateChanged += OnPlayModeStateChanged;
		}

		private void OnPlayModeStateChanged(PlayModeStateChange state)
		{
			if (state == PlayModeStateChange.ExitingEditMode || state == PlayModeStateChange.EnteredPlayMode)
			{
				foreach (var frame in SelectSyncFrames())
				{
					ClearTexture(frame);
				}
			}
		}

		void OnEnable()
		{
			_Instance = target as SyncFrameManager;
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

			EditorGUI.BeginDisabledGroup(Lock != null);
			{
				EditorGUILayout.LabelField("1. Spread Sheet URL には、次のようなスプレッドシートの URL を入力 (例) https://docs.google.com/spreadsheets/d/hoge/\n1列目をid、2列目を画像URL、3列目以降は自由です。", style);
				EditorGUILayout.LabelField("※ スプレッドシートの共有「リンクを知っている全員」「閲覧者」に必ずして下さい ※", bold);
				_Instance.SpreadSheetUrl = EditorGUILayout.TextField("Spread Sheet Url", _Instance.SpreadSheetUrl);
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("2. Work Sheet には、スプレッドシート下部のワークシート(タブ)の名前を入力", style);
				_Instance.WorkSheet = EditorGUILayout.TextField("Work Sheet", _Instance.WorkSheet);
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("3. スプレッドシートを読み込みます。", style);
				if (GUILayout.Button("読み込み！"))
				{
					LoadSheet();
					Lock = UpdatingSyncFrames(_Instance.SpreadSheetUrl, _Instance.WorkSheet);
					EditorCoroutine.Start(Lock);
				}
				EditorGUILayout.LabelField("");
			}
			EditorGUI.EndDisabledGroup();
			EditorGUI.BeginDisabledGroup(Lock != null || PhotoTable == null);
			{
				EditorGUILayout.LabelField("4. 画像をサーバーにアップロードします。これには数分かかります。", style);
				if (GUILayout.Button("アップロード！"))
				{
					Lock = UploadingPhotos();
					EditorCoroutine.Start(Lock);
				}
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("5. 子オブジェクトの Photo Frame のインスペクター内の id を表示したい画像のものを入力", style);
				EditorGUILayout.LabelField("Photo Frame Manager は、この子オブジェクトだけの画像を管理します", style);
				EditorGUILayout.LabelField("");

				EditorGUILayout.LabelField("6. 「設定！」で、スプレッドシートからURLの画像を読み込み仮表示", style);
				if (GUILayout.Button("表示！"))
				{
					Lock = AssigningPhotos();
					EditorCoroutine.Start(Lock);
				}
				EditorGUILayout.LabelField("");
			}
			EditorGUI.EndDisabledGroup();
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

		private IEnumerator UpdatingSyncFrames(string url, string worksheet)
		{
			string key = GetSpreadSheetKey(url);
			if (string.IsNullOrEmpty(key) || !Validate(key, worksheet)) yield break;

			foreach (var frame in SelectSyncFrames()) frame.AssignLoading();

			string api = BASE_URL + "sheet/" + key + "/" + worksheet + ".json";
			using (UnityWebRequest www = UnityWebRequest.Get(api))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.result != UnityWebRequest.Result.Success)
				{
					Debug.LogError("Sheet API: " + api + "\n" + www.error);
					Lock = null;
					yield break;
				}
				Dictionary<string, object> response = Json.Deserialize(www.downloadHandler.text) as Dictionary<string, object>;
				if (response == null || (string)response["status"] != "OK")
				{
					Debug.LogError("スプレッドシートからデータの読み込みに失敗しました\n" + www.downloadHandler.text);
					Lock = null;
					yield break;
				}
				PhotoTable = new Dictionary<string, PhotoItem>();
				foreach (var o in response["items"] as List<object>)
				{
					var item = PhotoItem.Parse(CurrentSheet, o as Dictionary<string, object>);
					if (item != null) PhotoTable[item.ID] = item;
				}
			}
			Debug.Log("読み込み完了！");
			Lock = null;
		}

		private IEnumerator UploadingPhotos()
		{
			foreach(PhotoItem item in PhotoTable.Values)
			{
				double start = EditorApplication.timeSinceStartup;
				while(EditorApplication.timeSinceStartup - start < 3.0) yield return new WaitForSeconds(1f);
				string key = CurrentSheet.SheetKey;
				string worksheet = CurrentSheet.Worksheet;
				string api = BASE_URL + "upload/" + key + "/" + worksheet + "/" + item.ID;
				Debug.Log(" Uploading=" + api);
				using (UnityWebRequest www = UnityWebRequest.Get(api))
				{
					yield return www.SendWebRequest();
					while (!www.isDone) yield return null;
					if (www.result != UnityWebRequest.Result.Success)
					{
						Debug.LogError(www.error);
					}
				}
			}
			Debug.Log("アップロード完了！");
			Lock = null;
		}

		private IEnumerator AssigningPhotos()
		{
			foreach(var frame in SelectSyncFrames())
			{
				EditorCoroutine.Start(AssigningWebTexture(frame));

				double start = EditorApplication.timeSinceStartup;
				while(EditorApplication.timeSinceStartup - start < 1.0) yield return new WaitForSeconds(1f);
			}
			Lock = null;
		}

		private IEnumerator ClearingSyncFrames(string url, string worksheet)
		{
			foreach (var frame in SelectSyncFrames())
			{
				ClearTexture(frame);
			}

			string key = GetSpreadSheetKey(url);
			if (string.IsNullOrEmpty(key) || !Validate(key, worksheet)) yield break;

			string api = BASE_URL + "delete/" + key + "/" + worksheet;
			Debug.Log(api);
			using (UnityWebRequest www = UnityWebRequest.Get(api))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.result != UnityWebRequest.Result.Success)
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

		private SyncFrame[] SelectSyncFrames()
		{
			if (_Instance == null) return new SyncFrame[] { };

			var frames = _Instance.transform.GetComponentsInChildren<SyncFrame>();
			foreach (var frame in frames)
			{
				if (string.IsNullOrEmpty(frame.ID)) continue;
			}
			return frames;
		}

		private IEnumerator AssigningWebTexture(SyncFrame frame)
		{
			PhotoItem item;
			if (PhotoTable.ContainsKey(frame.ID))
			{
				item = PhotoTable[frame.ID];
			}
			else
			{
				item = PhotoItem.Parse(CurrentSheet, frame.ID);
			}
			frame.Url = new VRCUrl(item.PublicUrl);

			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) yield break;

			using (UnityWebRequest www = UnityWebRequestTexture.GetTexture(frame.Url.Get()))
			{
				yield return www.SendWebRequest();
				while (!www.isDone) yield return null;
				if (www.result != UnityWebRequest.Result.Success)
				{
					Debug.LogError("Image URL: " + frame.Url.Get() + "\n" + www.error);
				}
				else
				{
					Material copied = new Material(renderer.sharedMaterial);
					Texture2D tex = ((DownloadHandlerTexture)www.downloadHandler).texture;
					copied.mainTexture = tex;
					renderer.sharedMaterial = copied;
					if (frame.AutoAdjustAspect)
						frame.AdjustTexture(tex, 2);
					else
						frame.DoneTexture(tex, 2);
				}
			}
		}

		private void ClearTexture(SyncFrame frame)
		{
			Renderer renderer = frame.GetComponent<Renderer>();
			if (renderer == null || renderer.sharedMaterial == null) return;

			renderer.sharedMaterial.mainTexture = null;
		}

		private void LoadEnv()
		{
			string path = System.IO.Path.Combine(Application.dataPath, "MikanDealer/SyncFrame/env.json");
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

		private void LoadSheet()
		{
			CurrentSheet = new FrameSheet()
			{
				EndPointUrl = BASE_URL.EndsWith("/") ? BASE_URL : BASE_URL + "/",
				SheetKey = GetSpreadSheetKey(_Instance.SpreadSheetUrl),
				Worksheet = _Instance.WorkSheet
			};
		}
	}
}